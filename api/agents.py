from fastapi import APIRouter, BackgroundTasks, Depends

from agents.tasks import run_calendar_agent, run_email_agent, test_agent_pulse
from core.auth import get_current_user
from core.user_registry import User

router = APIRouter()


@router.post("/trigger-agent")
async def trigger_agent_test(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(test_agent_pulse, "Hello from API")
    return {"message": "Agent triggered"}


@router.post("/run-agents/calendar")
async def trigger_calendar_check(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(run_calendar_agent, user_id=current_user.id)
    return {"message": "Calendar Agent activated", "user_id": current_user.id}


@router.post("/run-agents/email")
async def trigger_email_check(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    background_tasks.add_task(run_email_agent, user_id=current_user.id)
    return {"message": "Email Agent activated", "user_id": current_user.id}
