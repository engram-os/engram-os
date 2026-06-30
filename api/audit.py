from fastapi import APIRouter, Depends, Query

from agents.logger import verify_audit_chain, get_recent_logs
from core.auth import require_admin
from core.schemas import AuditVerifyResponse
from core.user_registry import User

router = APIRouter()


@router.get("/api/audit/verify", response_model=AuditVerifyResponse)
def audit_verify(current_user: User = Depends(require_admin)):
    """Walk the full audit log and verify every HMAC chain link is unbroken."""
    return verify_audit_chain()


@router.get("/api/audit/logs")
def audit_logs(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(require_admin),
):
    """Return the most recent audit log entries (newest first)."""
    rows = get_recent_logs(limit)
    return {
        "logs": [
            {"timestamp": r[0], "actor": r[1], "action": r[2], "details": r[3]}
            for r in rows
        ]
    }
