import logging
import datetime
from googleapiclient.discovery import build
from agents.auth import get_google_credentials

logger = logging.getLogger(__name__)


def get_calendar_service():
    """Authenticates using the token.json generated locally."""
    creds = get_google_credentials()
    if not creds:
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