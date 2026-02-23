import base64
import logging
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from agents.auth import get_google_credentials

logger = logging.getLogger(__name__)


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
            txt = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = txt['payload']
            headers = payload.get("headers")
            
            subject = [h['value'] for h in headers if h['name'] == 'Subject'][0]
            sender = [h['value'] for h in headers if h['name'] == 'From'][0]
            snippet = txt.get('snippet', '')

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
        subject = [h['value'] for h in headers if h['name'] == 'Subject'][0]

        # 2. Constructing the Message

        message = MIMEText(reply_body)
        message['to'] = [h['value'] for h in headers if h['name'] == 'From'][0]
        message['subject'] = subject if subject.startswith("Re:") else "Re: " + subject
        
        # Threading:

        message['In-Reply-To'] = [h['value'] for h in headers if h['name'] == 'Message-ID'][0]
        message['References'] = [h['value'] for h in headers if h['name'] == 'Message-ID'][0]

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