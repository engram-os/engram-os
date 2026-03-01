import base64
import logging
import os
import sqlite3
import datetime
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from agents.auth import get_google_credentials

logger = logging.getLogger(__name__)

_current_dir = os.path.dirname(os.path.abspath(__file__))
_root_dir = os.path.dirname(_current_dir)
_DBS_DIR = os.path.join(_root_dir, "data", "dbs")
_PROCESSED_DB = os.path.join(_DBS_DIR, "processed_emails.db")


def _init_processed_db() -> None:
    os.makedirs(_DBS_DIR, exist_ok=True)
    conn = sqlite3.connect(_PROCESSED_DB, check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS processed_emails "
        "(email_id TEXT PRIMARY KEY, draft_id TEXT, processed_at TEXT)"
    )
    conn.commit()
    conn.close()


_init_processed_db()


def is_email_processed(email_id: str) -> bool:
    """Return True if this email has already been acted on."""
    try:
        conn = sqlite3.connect(_PROCESSED_DB, check_same_thread=False)
        row = conn.execute(
            "SELECT 1 FROM processed_emails WHERE email_id = ?", (email_id,)
        ).fetchone()
        conn.close()
        return row is not None
    except Exception as e:
        logger.error(f"processed_emails lookup failed: {e}")
        return False


def record_processed_email(email_id: str, draft_id: str) -> None:
    """Record that a draft was created for this email.

    Must be called immediately after draft creation — before any follow-up
    actions like mark-as-read — so idempotency is locked in even if later
    steps fail.
    """
    try:
        conn = sqlite3.connect(_PROCESSED_DB, check_same_thread=False)
        conn.execute(
            "INSERT OR IGNORE INTO processed_emails (email_id, draft_id, processed_at) VALUES (?, ?, ?)",
            (email_id, draft_id, datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to record processed email {email_id}: {e}")


def _get_header(headers: list, name: str, default: str = "") -> str:
    """Safely extract an email header value by name.

    Returns `default` if the header is missing rather than raising IndexError.
    Email headers are not guaranteed to exist — treating an absent header as a
    crash condition causes one malformed email to abort an entire batch.
    """
    return next((h['value'] for h in headers if h['name'] == name), default)


def get_gmail_service():
    creds = get_google_credentials()
    if not creds:
        return None

    return build('gmail', 'v1', credentials=creds)

def fetch_unread_emails(limit=5):
    service = get_gmail_service()
    if not service: return []

    try:

        # Getting list of unread messages from Inbox

        results = service.users().messages().list(userId='me', labelIds=['INBOX', 'UNREAD'], maxResults=limit).execute()
        messages = results.get('messages', [])
        
        email_data = []
        for msg in messages:
            txt = service.users().messages().get(userId='me', id=msg['id'], format='metadata', metadataHeaders=['Subject', 'From']).execute()
            payload = txt['payload']
            headers = payload.get("headers")
            
            subject = _get_header(headers, 'Subject', '(No Subject)')
            sender = _get_header(headers, 'From')
            snippet = txt.get('snippet', '')

            if not sender:
                logger.warning(f"Email {msg['id']} has no From header — skipping.")
                continue

            email_data.append({
                "id": msg['id'],
                "sender": sender,
                "subject": subject,
                "body": snippet
            })
            
        return email_data
    except Exception as e:
        logger.error(f"Gmail Read Error: {e}")
        return []

def create_draft_reply(email_id, reply_body):
    service = get_gmail_service()
    if not service: return {"status": "error"}

    try:

        # 1. Getting original email details to thread correctly 

        original = service.users().messages().get(userId='me', id=email_id).execute()
        headers = original['payload']['headers']
        subject = _get_header(headers, 'Subject', '(No Subject)')
        recipient = _get_header(headers, 'From')
        message_id = _get_header(headers, 'Message-ID')

        # 2. Constructing the Message

        message = MIMEText(reply_body)
        message['to'] = recipient
        message['subject'] = subject if subject.startswith("Re:") else "Re: " + subject

        # Threading: only set if Message-ID exists — omitting is valid per RFC 2822.
        if message_id:
            message['In-Reply-To'] = message_id
            message['References'] = message_id

        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        body = {
            'message': {
                'raw': raw_message,
                'threadId': original['threadId']
            }
        }

        draft = service.users().drafts().create(userId='me', body=body).execute()
        logger.info(f"DRAFT SAVED: {draft['id']}")
        return {"status": "success", "draft_id": draft['id']}

    except Exception as e:
        logger.error(f"Draft Error: {e}")
        return {"status": "error", "details": str(e)}


def mark_email_as_read(email_id: str) -> bool:
    """Remove the UNREAD label from a message.

    Best-effort: always called after record_processed_email so a failure here
    does not cause re-processing. Returns True on success, False on failure.
    """
    service = get_gmail_service()
    if not service:
        return False
    try:
        service.users().messages().modify(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
        logger.info(f"Marked {email_id} as read.")
        return True
    except Exception as e:
        logger.error(f"Failed to mark {email_id} as read (non-critical): {e}")
        return False