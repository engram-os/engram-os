import os.path
import logging
import datetime
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """Authenticates using the token.json generated locally."""
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logger.error("Token expired or missing. Run generate_token.py on Host.")
            return None

    return build('calendar', 'v3', credentials=creds)

def add_calendar_event(title: str, time: str, description: str = ""):
    """
    Creates a real event on Google Calendar.
    NOTE: For this demo, we default to 'Tomorrow' to avoid complex date parsing logic.
    """
    service = get_calendar_service()
    if not service:
        return {"status": "error", "message": "Authentication failed"}

    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    day_after = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()

    event_body = {
        'summary': title,
        'description': f"{description}\n\n(Context: {time})\n(Scheduled by Engram AI)",
        'start': {
            'date': tomorrow, 
            'timeZone': 'UTC',
        },
        'end': {
            'date': day_after,
            'timeZone': 'UTC',
        },
    }

    try:
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        link = event.get('htmlLink')
        logger.info(f"REAL EVENT CREATED: {link}")
        return {"status": "success", "link": link}
    except Exception as e:
        logger.error(f"Google API Error: {e}")
        return {"status": "error", "details": str(e)}