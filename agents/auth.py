import os
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

TOKEN_PATH = os.getenv("GOOGLE_TOKEN_PATH", "credentials/token.json")

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
]


def get_google_credentials():
    """Load and refresh Google OAuth credentials. Returns None if unavailable."""
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            logger.error("Google token missing or expired. Run scripts/generate_token.py.")
            return None

    return creds
