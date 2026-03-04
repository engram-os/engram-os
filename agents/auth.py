import os
import logging
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
]


def _resolve_token_path(user_id: str) -> str:
    """Return the token.json path to use for this user.

    Priority:
      1. GOOGLE_TOKEN_PATH env override (used in Docker / CI).
      2. Per-user path credentials/{user_id}/token.json (if file exists).
      3. Shared fallback credentials/token.json.
    """
    env_override = os.getenv("GOOGLE_TOKEN_PATH", "")
    if env_override:
        return env_override
    if user_id:
        per_user = f"credentials/{user_id}/token.json"
        if os.path.exists(per_user):
            return per_user
    return "credentials/token.json"


def get_google_credentials(user_id: str = ""):
    """Load and refresh Google OAuth credentials. Returns None if unavailable."""
    token_path = _resolve_token_path(user_id)
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, "w") as f:
                f.write(creds.to_json())
            logger.info("Google OAuth token refreshed and persisted.")
        else:
            logger.error("Google token missing or expired. Run scripts/generate_token.py.")
            return None

    return creds
