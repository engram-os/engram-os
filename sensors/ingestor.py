import os
import signal
import sys
import time
import shutil
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from core.network_gateway import gateway
import logging
import re
import pypdf
import docx
import openpyxl
from core.identity import get_or_create_identity

_PDF_PARSE_TIMEOUT = int(os.getenv("PDF_PARSE_TIMEOUT", "30"))  # seconds

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

INBOX_DIR = os.path.join(root_dir, "data", "inbox")
PROCESSED_DIR = os.path.join(INBOX_DIR, "processed")
FAILED_DIR = os.path.join(INBOX_DIR, "failed")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

IDENTITY = get_or_create_identity()
LOCAL_USER_ID = IDENTITY["user_id"]

_api_key = os.getenv("ENGRAM_API_KEY", "")
_API_HEADERS = {"X-API-Key": _api_key} if _api_key else {}

os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)
os.makedirs(FAILED_DIR, exist_ok=True)

PATTERNS = {
    "insurer":      r"(?i)(?:claim\s+denial\s+notice|prior\s+authorization[\w\s]*)\s*[—\-]+\s*(.+)",
    "claim_number": r"(?i)claim\s*(?:number|#|no\.?)\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-]+)",
    "auth_number":  r"(?i)authorization\s+number\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-]+)",
    "reference":    r"(?i)reference(?:\s*(?:number|no\.?))?\s*[:\-]?\s*([A-Z0-9][A-Z0-9\-]+)",
    "patient":      r"(?i)patient\s*[:\-]\s*([A-Z][A-Z\-]+)",
    "dos":          r"(?i)date\s+of\s+service\s*[:\-]\s*(\d{4}-\d{2}-\d{2})",
    "cpt_code":     r"(?i)CPT\s*[:\-]?\s*(\d{5})",
    "icd10":        r"\b([A-Z]\d{2}\.\d{1,4})\b",
    "denial_code":  r"(?i)\b(CO-\d+|PR-\d+|OA-\d+|PI-\d+)\b",
}

def extract_document_keys(text: str) -> dict:
    """Extract structured identifiers for composite identity and discriminative embedding."""
    keys = {}
    for field, pattern in PATTERNS.items():
        match = re.search(pattern, text)
        if match:
            keys[field] = match.group(1).strip()
    return keys

def _parse_pdf(filepath: str, filename: str) -> str:
    """Extract text from all pages of a PDF. Runs in a thread for timeout enforcement."""
    reader = pypdf.PdfReader(filepath)
    parts = [page.extract_text() or "" for page in reader.pages]
    return f"File '{filename}': " + "\n".join(parts)


def extract_text(filepath):
    """Smart text extractor for PDF and Text files."""
    filename = os.path.basename(filepath)
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == '.pdf':
            pool = ThreadPoolExecutor(max_workers=1)
            future = pool.submit(_parse_pdf, filepath, filename)
            try:
                result = future.result(timeout=_PDF_PARSE_TIMEOUT)
                pool.shutdown(wait=False)
                return result
            except FuturesTimeoutError:
                logger.error(f"PDF parse timed out after {_PDF_PARSE_TIMEOUT}s: {filename}")
                pool.shutdown(wait=False)  # don't block — thread may still be running
                return None
            
        elif ext == '.docx':
            doc = docx.Document(filepath)
            text = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            return f"File '{filename}': {text}"

        elif ext == '.xlsx':
            wb = openpyxl.load_workbook(filepath, read_only=True, data_only=True)
            parts = []
            for sheet in wb.worksheets:
                rows = []
                for row in sheet.iter_rows():
                    cells = [str(cell.value) for cell in row if cell.value is not None]
                    if cells:
                        rows.append("\t".join(cells))
                if rows:
                    parts.append(f"[Sheet: {sheet.title}]\n" + "\n".join(rows))
            wb.close()
            return f"File '{filename}':\n" + "\n\n".join(parts) if parts else None

        elif ext in ['.txt', '.md', '.py', '.js', '.ts', '.csv', '.json',
                     '.yaml', '.yml', '.html', '.xml', '.rst']:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f"File '{filename}': {f.read()}"

        else:
            return None
    except Exception as e:
        logger.error(f"Failed to read {filename}: {e}")
        return None

def _build_embed_text(keys: dict) -> str | None:
    """Build a natural language embed sentence from extracted keys.

    Key:value format embeds in a different region of the vector space than
    natural language queries. Since deduplication is handled by the composite
    key hash (SHA256), embed_text can be optimised purely for retrieval.
    """
    if not keys:
        return None
    parts = []
    if "insurer" in keys:
        parts.append(keys["insurer"])
    patient = keys.get("patient", "")
    if patient:
        # LAST-FIRST → First Last
        name_parts = patient.replace("-", " ").split()
        if len(name_parts) == 2:
            patient_nl = f"{name_parts[1]} {name_parts[0]}".title()
        else:
            patient_nl = patient.replace("-", " ").title()
        parts.append(f"claim for {patient_nl}")
    if "claim_number" in keys:
        parts.append(f"claim number {keys['claim_number']}")
    if "auth_number" in keys:
        parts.append(f"authorization number {keys['auth_number']}")
    if "denial_code" in keys:
        parts.append(f"denied with code {keys['denial_code']}")
    if "cpt_code" in keys:
        parts.append(f"CPT {keys['cpt_code']}")
    if "icd10" in keys:
        parts.append(keys["icd10"])
    return " ".join(parts) if parts else None


def _quarantine(filepath: str, reason: str) -> None:
    """Move a file to FAILED_DIR with a reason suffix so failures are inspectable."""
    filename = os.path.basename(filepath)
    root, ext = os.path.splitext(filename)
    dest = os.path.join(FAILED_DIR, f"{root}_{reason}{ext}")
    if os.path.exists(dest):
        dest = os.path.join(FAILED_DIR, f"{root}_{reason}_{int(time.time() * 1000)}{ext}")
    try:
        shutil.move(filepath, dest)
        logger.warning("   Quarantined → failed/%s", os.path.basename(dest))
    except Exception as e:
        logger.error("   Could not quarantine %s: %s", filename, e)


def scan_inbox():
    if not os.path.exists(INBOX_DIR):
        logger.error("Inbox directory not found: %s", INBOX_DIR)
        return

    try:
        files = [f for f in os.listdir(INBOX_DIR) if os.path.isfile(os.path.join(INBOX_DIR, f))]
    except Exception as e:
        logger.error("Error reading inbox: %s", e)
        return

    if not files:
        return

    had_error = False
    for filename in files:
        if filename.startswith("."):
            continue

        filepath = os.path.join(INBOX_DIR, filename)
        size_kb = os.path.getsize(filepath) / 1024
        ext = os.path.splitext(filename)[1].lower()
        logger.info("Detected: %s (%.1f KB, type=%s)", filename, size_kb, ext or "none")

        t0 = time.monotonic()
        try:
            content = extract_text(filepath)
        except Exception as e:
            logger.error("   Parse error for %s: %s", filename, e)
            _quarantine(filepath, "parse_error")
            continue
        parse_ms = int((time.monotonic() - t0) * 1000)

        if content is None:
            logger.warning("   Unsupported file type: %s (%.0f ms)", filename, parse_ms)
            _quarantine(filepath, "unsupported")
            continue

        logger.info("   Parsed in %d ms, %d chars", parse_ms, len(content))

        try:
            keys = extract_document_keys(content)
            embed_text = _build_embed_text(keys)
            if keys:
                logger.info("   Keys extracted: %s", keys)
            else:
                logger.warning("   No structured keys found — falling back to content hash")

            res = gateway.post("brain", "/ingest", json={
                "text": content,
                "user_id": LOCAL_USER_ID,
                "type": "file_ingest",
                "embed_text": embed_text,
                "document_keys": keys,
            }, headers=_API_HEADERS, timeout=(5, 10))

            if res.status_code == 200:
                body = res.json()
                if body.get("status") == "duplicate_skipped":
                    logger.warning("   Duplicate skipped (already stored): %s", filename)
                else:
                    logger.info("   Ingested as new memory (id=%s)", body.get("id", "?"))

                destination = os.path.join(PROCESSED_DIR, filename)
                if os.path.exists(destination):
                    timestamp = int(time.time() * 1000)
                    root, ext = os.path.splitext(filename)
                    destination = os.path.join(PROCESSED_DIR, f"{root}_{timestamp}{ext}")

                shutil.move(filepath, destination)
                logger.info("   -> Moved to processed/")
            else:
                logger.error("   API error %s for %s — will retry next poll", res.status_code, filename)
                had_error = True

        except Exception as e:
            logger.error("   Connection failed (Is the Brain online?): %s", e)
            had_error = True

    return had_error

def _handle_shutdown(sig, frame):
    logger.info(f"Received signal {sig}. File watcher shutting down cleanly.")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _handle_shutdown)
    signal.signal(signal.SIGINT, _handle_shutdown)

    print("------------------------------------------------")
    logger.info(f"File Watcher Active.")
    logger.info(f"Watching: {INBOX_DIR}")
    logger.info(f"Drop files there to ingest them.")
    print("------------------------------------------------")
    
    BASE_SLEEP = 5
    MAX_SLEEP = 300
    consecutive_errors = 0

    while True:
        had_error = scan_inbox()
        if had_error:
            consecutive_errors += 1
            sleep_for = min(BASE_SLEEP * (2 ** consecutive_errors), MAX_SLEEP)
            logger.warning(f"API errors detected. Backing off for {sleep_for}s (attempt {consecutive_errors})")
        else:
            consecutive_errors = 0
            sleep_for = BASE_SLEEP
        time.sleep(sleep_for)