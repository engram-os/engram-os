from fastapi import APIRouter, Depends, HTTPException, Query

from agents.logger import log_agent_action
from core.auth import get_current_user, require_admin
from core.deps import COLLECTION_NAME, client
from core.matter_registry import (
    bootstrap_default_matter,
    check_access,
    close_matter as registry_close_matter,
    create_matter as registry_create_matter,
    get_matter,
    grant_access,
    list_matters_for_user,
)
from core.user_registry import User
from qdrant_client.http import models

router = APIRouter()


def _resolve_matter(user: User, matter_id: str | None) -> str | None:
    """Validate matter access and return the resolved matter_id.

    Returns None when matter_id is None — this means 'no filter', preserving
    full backwards compatibility with untagged legacy data.
    """
    if matter_id is None:
        return None
    matter = get_matter(matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail=f"Matter '{matter_id}' not found.")
    if matter["status"] == "closed":
        raise HTTPException(status_code=410, detail=f"Matter '{matter_id}' is closed.")
    if user.role != "admin" and not check_access(user.id, matter_id):
        raise HTTPException(status_code=403, detail="Access denied to this matter.")
    return matter_id


@router.get("/api/matters")
def get_matters(current_user: User = Depends(get_current_user)):
    return {"matters": list_matters_for_user(current_user.id)}


@router.post("/api/matters")
def new_matter(
    name: str = Query(..., min_length=1, max_length=200),
    current_user: User = Depends(get_current_user),
):
    try:
        matter_id = registry_create_matter(name=name, created_by=current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"matter_id": matter_id, "name": name}


@router.post("/api/matters/{matter_id}/close")
def close_matter_endpoint(matter_id: str, current_user: User = Depends(get_current_user)):
    matter = get_matter(matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail=f"Matter '{matter_id}' not found.")
    if matter["status"] == "closed":
        raise HTTPException(status_code=410, detail=f"Matter '{matter_id}' is already closed.")
    if current_user.role != "admin" and matter["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="Only the matter owner or an admin can close it.")

    deleted_count = 0
    offset = None
    while True:
        batch, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(must=[
                models.FieldCondition(key="matter_id", match=models.MatchValue(value=matter_id)),
            ]),
            limit=100,
            offset=offset,
            with_payload=False,
        )
        if not batch:
            break
        ids = [p.id for p in batch]
        client.delete(
            collection_name=COLLECTION_NAME,
            points_selector=models.PointIdsList(points=ids),
        )
        deleted_count += len(ids)
        offset = next_offset
        if not next_offset:
            break

    registry_close_matter(matter_id, closed_by=current_user.id)
    log_agent_action(
        f"user:{current_user.id}", "DELETE",
        f"matter_closed:{matter_id}:{deleted_count}_points",
        resource_id=matter_id,
    )
    return {"matter_id": matter_id, "deleted_points": deleted_count}


@router.post("/api/matters/{matter_id}/access")
def grant_matter_access(
    matter_id: str,
    user_id: str = Query(..., min_length=1, max_length=100),
    _admin: User = Depends(require_admin),
):
    matter = get_matter(matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail=f"Matter '{matter_id}' not found.")
    grant_access(matter_id=matter_id, user_id=user_id, granted_by=_admin.id)
    return {"status": "access_granted", "matter_id": matter_id, "user_id": user_id}
