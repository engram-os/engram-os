from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from core.auth import get_current_user, require_admin
from core.user_registry import User, create_user, list_users

router = APIRouter()


class UserCreateRequest(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field(default="user")


@router.get("/api/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {"id": current_user.id, "role": current_user.role, "display_name": current_user.display_name}


@router.post("/api/users")
def create_new_user(body: UserCreateRequest, _admin: User = Depends(require_admin)):
    if body.role not in ("admin", "user"):
        raise HTTPException(status_code=422, detail="role must be 'admin' or 'user'.")
    user_id, raw_key = create_user(display_name=body.display_name, role=body.role)
    return {"user_id": user_id, "api_key": raw_key, "display_name": body.display_name}


@router.get("/api/users")
def list_all_users(_admin: User = Depends(require_admin)):
    return {"users": list_users()}
