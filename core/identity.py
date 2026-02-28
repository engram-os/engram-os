import uuid
import os
import json
import datetime

IDENTITY_FILE = os.path.expanduser("~/.engram/identity.json")

def get_or_create_identity() -> dict:
    env_user_id = os.getenv("ENGRAM_USER_ID")
    if env_user_id:
        return {"user_id": env_user_id, "source": "env"}

    if os.path.exists(IDENTITY_FILE):
        with open(IDENTITY_FILE, "r") as f:
            return json.load(f)

    identity = {
        "user_id": str(uuid.uuid4()),
        "created_at": str(datetime.datetime.now()),
        "machine": os.uname().nodename
    }

    os.makedirs(os.path.dirname(IDENTITY_FILE), exist_ok=True)
    with open(IDENTITY_FILE, "w") as f:
        json.dump(identity, f, indent=2)
    os.chmod(IDENTITY_FILE, 0o600)

    return identity
