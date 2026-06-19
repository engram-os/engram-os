#!/usr/bin/env python3
"""
Sovereign Agent Audit in a Box.

MAP constraints:
- Local-only execution.
- Sequential script that presents as Planner -> Redactor -> Auditor.
- Regex PII redaction.
- Best-effort local Ollama summary with deterministic fallback.
- Fake ZK proof: SHA-256 hash of audit_log.jsonl.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib import request

try:
    from pypdf import PdfReader
except Exception:  # pragma: no cover - fallback supports smoke tests without deps
    PdfReader = None


ROOT = Path(__file__).resolve().parent
DEFAULT_INPUT = ROOT / "input"
DEFAULT_OUTPUT = ROOT / "outputs" / "latest"
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")


PII_PATTERNS = [
    ("email", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)),
    ("phone", re.compile(r"(?<!\d)(?:\+?1[\s.-]?)?(?:\(?\d{3}\)?[\s.-]?)\d{3}[\s.-]?\d{4}(?!\d)")),
    ("ssn", re.compile(r"\b\d{3}-\d{2}-\d{4}\b")),
    ("iban_like", re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{10,30}\b")),
    ("street_address", re.compile(r"\b\d{1,6}\s+[A-Za-z0-9 .'-]+\s+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr)\b", re.I)),
]

ANOMALY_PATTERNS = [
    ("indemnity", r"\bindemnif(?:y|ication)\b", "Indemnity language found. Check scope, caps, and mutuality."),
    ("unlimited_liability", r"\bunlimited liability\b", "Unlimited liability found. High-risk commercial term."),
    ("auto_renewal", r"\bauto(?:matic)? renewal\b|\brenews automatically\b", "Auto-renewal clause found. Confirm notice window."),
    ("termination_for_convenience", r"\btermination for convenience\b", "Termination-for-convenience clause found. Validate economics."),
    ("governing_law", r"\bgoverned by the laws of\b", "Governing law clause found. Confirm jurisdiction fit."),
    ("data_processing", r"\bpersonal data\b|\bprotected health information\b|\bPHI\b|\bHIPAA\b", "Sensitive data processing language found."),
    ("non_compete", r"\bnon-compete\b|\bnoncompete\b", "Non-compete language found. Review enforceability."),
    ("assignment", r"\bassign(?:ment)?\b", "Assignment language found. Check change-of-control treatment."),
]


@dataclass
class AuditEvent:
    ts: str
    agent: str
    action: str
    detail: str
    elapsed_ms: int


class AuditRun:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.audit_log = self.output_dir / "audit_log.jsonl"
        self.events: list[AuditEvent] = []
        self.started = time.monotonic()

    def log(self, agent: str, action: str, detail: str) -> None:
        event = AuditEvent(
            ts=datetime.now(timezone.utc).isoformat(),
            agent=agent,
            action=action,
            detail=detail,
            elapsed_ms=int((time.monotonic() - self.started) * 1000),
        )
        self.events.append(event)
        with self.audit_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
        print(f"[{agent}] {action}: {detail}")


def read_pdf(path: Path) -> str:
    if PdfReader is None:
        return path.read_text(encoding="utf-8", errors="ignore")
    reader = PdfReader(str(path))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def ingest_pdf(input_dir: Path, run: AuditRun) -> list[dict]:
    docs = []
    pdfs = sorted(input_dir.glob("*.pdf"))
    txts = sorted(input_dir.glob("*.txt"))
    run.log("Planner", "scan_input", f"Found {len(pdfs)} PDFs and {len(txts)} text files in {input_dir}")

    for path in [*pdfs, *txts]:
        started = time.monotonic()
        try:
            text = read_pdf(path) if path.suffix.lower() == ".pdf" else path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            run.log("Planner", "ingest_error", f"{path.name}: {exc}")
            continue
        docs.append({"name": path.name, "text": text, "chars": len(text)})
        run.log("Planner", "ingest_pdf", f"{path.name}: {len(text)} chars in {int((time.monotonic() - started) * 1000)}ms")
    return docs


def redact_pii(docs: list[dict], run: AuditRun) -> tuple[list[dict], dict[str, int]]:
    counts = {name: 0 for name, _pattern in PII_PATTERNS}
    redacted_docs = []
    for doc in docs:
        text = doc["text"]
        for name, pattern in PII_PATTERNS:
            text, n = pattern.subn(f"[REDACTED_{name.upper()}]", text)
            counts[name] += n
        redacted_docs.append({**doc, "redacted_text": text})
        run.log("Redactor", "redact_pii", f"{doc['name']}: redacted with local regex rules")
    return redacted_docs, counts


def flag_anomaly(docs: list[dict], run: AuditRun) -> list[dict]:
    findings = []
    for doc in docs:
        text = doc["redacted_text"]
        for code, pattern, message in ANOMALY_PATTERNS:
            matches = list(re.finditer(pattern, text, re.I))
            if not matches:
                continue
            finding = {
                "document": doc["name"],
                "code": code,
                "count": len(matches),
                "severity": "high" if code in {"unlimited_liability", "data_processing", "non_compete"} else "medium",
                "message": message,
                "snippet": text[max(0, matches[0].start() - 120): matches[0].end() + 120].replace("\n", " "),
            }
            findings.append(finding)
            run.log("Auditor", "flag_anomaly", f"{doc['name']}: {code} x{len(matches)}")
    return findings


def try_ollama(prompt: str, timeout_sec: int = 8) -> str | None:
    payload = json.dumps({"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}).encode("utf-8")
    req = request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=timeout_sec) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body.get("response", "").strip() or None
    except Exception:
        return None


def deterministic_summary(docs: list[dict], findings: list[dict], pii_counts: dict[str, int]) -> str:
    high = [f for f in findings if f["severity"] == "high"]
    medium = [f for f in findings if f["severity"] == "medium"]
    lines = [
        "Sovereign Agent Contract Audit",
        "",
        f"Documents reviewed: {len(docs)}",
        f"Total characters reviewed locally: {sum(d['chars'] for d in docs)}",
        f"PII redactions: {sum(pii_counts.values())} ({', '.join(f'{k}: {v}' for k, v in pii_counts.items())})",
        f"Findings: {len(high)} high, {len(medium)} medium",
        "",
        "Top findings:",
    ]
    if findings:
        for item in findings[:15]:
            lines.append(f"- [{item['severity'].upper()}] {item['document']}: {item['message']} ({item['count']} match/es)")
    else:
        lines.append("- No configured high-liability terms were detected in the supplied documents.")
    lines.extend([
        "",
        "Recommended next step:",
        "Schedule a 30-minute attorney/operator review to validate flagged clauses before signature.",
    ])
    return "\n".join(lines)


def generate_summary(docs: list[dict], findings: list[dict], pii_counts: dict[str, int], run: AuditRun) -> str:
    compact_findings = json.dumps(findings[:20], indent=2)
    prompt = (
        "You are Engram's Auditor agent. Produce a concise contract risk summary for a paid pilot. "
        "Do not reveal PII. Include document count, risk themes, and next steps.\n\n"
        f"Documents: {len(docs)}\nPII counts: {pii_counts}\nFindings:\n{compact_findings}"
    )
    summary = try_ollama(prompt)
    if summary:
        run.log("Auditor", "generate_summary", f"Generated summary with local Ollama model {OLLAMA_MODEL}")
        return summary
    run.log("Auditor", "generate_summary", "Ollama unavailable or timed out; used deterministic local fallback")
    return deterministic_summary(docs, findings, pii_counts)


def write_outputs(output_dir: Path, docs: list[dict], findings: list[dict], pii_counts: dict[str, int], summary: str, run: AuditRun) -> None:
    redacted_dir = output_dir / "redacted"
    redacted_dir.mkdir(exist_ok=True)
    for doc in docs:
        (redacted_dir / f"{Path(doc['name']).stem}.redacted.txt").write_text(doc["redacted_text"], encoding="utf-8")

    (output_dir / "summary.txt").write_text(summary + "\n", encoding="utf-8")
    (output_dir / "findings.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
    (output_dir / "pii_counts.json").write_text(json.dumps(pii_counts, indent=2), encoding="utf-8")

    run.log("Auditor", "fake_zk_proof", "SHA-256 proof generated from complete local audit log")
    proof_hash = hashlib.sha256(run.audit_log.read_bytes()).hexdigest()
    proof = {
        "proof_type": "fake_zk_sha256_audit_log_hash",
        "not_real_zk": True,
        "algorithm": "sha256",
        "audit_log": "audit_log.jsonl",
        "hash": proof_hash,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_dir / "proof.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    (output_dir / "status.json").write_text(
        json.dumps(
            {
                "summary": summary,
                "proof": proof,
                "events": [asdict(event) for event in run.events],
                "finding_count": len(findings),
                "document_count": len(docs),
                "pii_redaction_count": sum(pii_counts.values()),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"[Auditor] proof_hash: {proof_hash}")


def reset_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    for child in path.iterdir():
        if child.is_dir():
            for nested in child.glob("*"):
                nested.unlink()
            child.rmdir()
        else:
            child.unlink()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Engram Sovereign Agent Audit MAP.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Folder containing 10-50 PDFs or text smoke-test docs.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Output folder for summary, logs, proof, and dashboard data.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    reset_output_dir(args.output)
    run = AuditRun(args.output)
    run.log("Planner", "start", "Audit plan: ingest_pdf -> redact_pii -> flag_anomaly -> generate_summary")
    docs = ingest_pdf(args.input, run)
    if not docs:
        run.log("Planner", "no_documents", "Add PDFs or text files to input/ and rerun ./run_audit.sh")
        return 2
    redacted_docs, pii_counts = redact_pii(docs, run)
    findings = flag_anomaly(redacted_docs, run)
    summary = generate_summary(redacted_docs, findings, pii_counts, run)
    write_outputs(args.output, redacted_docs, findings, pii_counts, summary, run)
    print(f"\nDone. Open dashboard at http://localhost:8000/dashboard/")
    print(f"Summary: {args.output / 'summary.txt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
