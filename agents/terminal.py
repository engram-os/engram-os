import asyncio
import logging
import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from core.auth import get_current_user
from core.network_gateway import gateway
from core.user_registry import User

logger = logging.getLogger(__name__)
router = APIRouter()
LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")


class TerminalRequest(BaseModel):
    command: str = Field(..., min_length=1, max_length=2_000)

@router.post("/api/terminal/fix")
async def fix_terminal_command(request: TerminalRequest, _: User = Depends(get_current_user)):
    logger.debug("Terminal fix request received")

    prompt = f"""
    You are a ZSH/Bash terminal expert.
    The user tried to run this command but it failed:
    "{request.command}"

    Fix the syntax, typo, or logic error.
    Output ONLY the corrected command string. Do not add markdown, quotes, or explanations.
    """

    try:
        res = await asyncio.to_thread(
            gateway.post, "ollama", "/api/chat",
            json={"model": LLM_MODEL, "messages": [{"role": "user", "content": prompt}], "stream": False},
            timeout=60,
        )
        fixed_command = res.json()["message"]["content"].strip()
        fixed_command = fixed_command.replace('`', '').strip()
        return {"fixed_command": fixed_command}

    except Exception as e:
        print(f"Genie Error: {e}")
        return {"fixed_command": request.command}
