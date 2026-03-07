import logging
import datetime
from googleapiclient.discovery import build
from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError
from agents.auth import get_google_credentials

logger = logging.getLogger(__name__)


def get_calendar_service():
    """Authenticates using the token.json generated locally."""
    creds = get_google_credentials()
    if not creds:
        return None

    return build('calendar', 'v3', credentials=creds)

def add_calendar_event(title: str, time: str, description: str = ""):
    """Creates a real event on Google Calendar.

    Parses the `time` string using dateutil (fuzzy mode) to support natural
    language like "next Thursday at 2pm" or "Friday morning". Falls back to
    tomorrow if parsing fails.
    """
    service = get_calendar_service()
    if not service:
        return {"status": "error", "message": "Authentication failed"}

    # Parse the LLM-extracted time string.
    # Sentinel default: 22:47 is an unusual time unlikely to appear in natural language.
    # If dateutil fills this default, no time was specified in the string.
    # This correctly handles "midnight" (00:00), which the old `hour != 0` check misclassified.
    _SENTINEL_HOUR, _SENTINEL_MIN = 22, 47
    sentinel = datetime.datetime.now().replace(
        hour=_SENTINEL_HOUR, minute=_SENTINEL_MIN, second=0, microsecond=0
    )
    try:
        parsed_dt = dateutil_parser.parse(time, fuzzy=True, default=sentinel)
        # If the parsed time is in the past, assume next occurrence (+7 days)
        if parsed_dt < datetime.datetime.now():
            parsed_dt += datetime.timedelta(days=7)
    except (ParserError, ValueError):
        logger.warning(f"Could not parse time string {time!r} — defaulting to tomorrow.")
        parsed_dt = datetime.datetime.now() + datetime.timedelta(days=1)

    # Use dateTime (timed) if a specific time was given, otherwise all-day date.
    has_time_component = not (parsed_dt.hour == _SENTINEL_HOUR and parsed_dt.minute == _SENTINEL_MIN)
    if has_time_component:
        start = {"dateTime": parsed_dt.isoformat(), "timeZone": "UTC"}
        end = {"dateTime": (parsed_dt + datetime.timedelta(hours=1)).isoformat(), "timeZone": "UTC"}
    else:
        start = {"date": parsed_dt.date().isoformat(), "timeZone": "UTC"}
        end = {"date": (parsed_dt + datetime.timedelta(days=1)).date().isoformat(), "timeZone": "UTC"}

    event_body = {
        'summary': title,
        'description': f"{description}\n\n(Scheduled by Engram AI)",
        'start': start,
        'end': end,
    }

    try:
        event = service.events().insert(calendarId='primary', body=event_body).execute()
        link = event.get('htmlLink')
        logger.info(f"REAL EVENT CREATED: {link}")
        return {"status": "success", "link": link}
    except Exception as e:
        logger.error(f"Google API Error: {e}")
        return {"status": "error", "details": str(e)}