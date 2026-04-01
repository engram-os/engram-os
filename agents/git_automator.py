import asyncio
import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from core.auth import get_current_user
from core.network_gateway import gateway
from core.user_registry import User

router = APIRouter()

class GitRequest(BaseModel):
    diff: str = Field(..., min_length=1, max_length=10_000)
    context: str = Field(default="", max_length=2_000)

@router.post("/api/git/commit-msg")
async def generate_commit(request: GitRequest, _: User = Depends(get_current_user)):
    if not request.diff.strip():
        raise HTTPException(status_code=400, detail="No changes detected in diff.")

    prompt = f"""
    You are a rigorous Git Commit Message Generator.
    Output ONLY the raw commit message.

    Rules:
    1. Do NOT include conversational text like "Here is the message".
    2. Do NOT use Markdown code blocks.
    3. Start directly with the type (feat:, fix:, chore:).
    4. Use imperative mood and keep it under 72 chars.

    Diff:
    {request.diff[:4000]}
    """

    res = await asyncio.to_thread(
        gateway.post, "ollama", "/api/chat",
        json={"model": "llama3.1:latest", "messages": [{"role": "user", "content": prompt}], "stream": False},
        timeout=60,
    )
    raw_msg = res.json()["message"]["content"].strip()
    clean_msg = raw_msg.replace("Here is the commit message:", "").replace("Here's the commit message:", "").strip()
    clean_msg = clean_msg.strip('"`')
    return {"message": clean_msg}

@router.post("/api/git/pr-description")
async def generate_pr(request: GitRequest, _: User = Depends(get_current_user)):
    prompt = f"""
    Write a structured Pull Request description for these changes.

    Structure:
    ## Summary
    [One sentence summary]

    ## Key Changes
    - [Bullet point]
    - [Bullet point]

    ## Tech Stack / Impact
    [Brief technical note]

    Diff:
    {request.diff[:6000]}
    """

    res = await asyncio.to_thread(
        gateway.post, "ollama", "/api/chat",
        json={"model": "llama3.1:latest", "messages": [{"role": "user", "content": prompt}], "stream": False},
        timeout=60,
    )
    return {"markdown": res.json()["message"]["content"]}

@router.post("/api/git/safety-check")
async def safety_check(request: GitRequest, _: User = Depends(get_current_user)):
    patterns = {
        "AWS Key": r"AKIA[0-9A-Z]{16}",
        "Private Key": r"-----BEGIN PRIVATE KEY-----",
        "Generic API Key": r"api_key\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]",
        "GitHub Token": r"ghp_[a-zA-Z0-9]{36}"
    }

    leaks = []
    for name, pattern in patterns.items():
        if re.search(pattern, request.diff):
            leaks.append(name)

    if leaks:
        return {"safe": False, "leaks": leaks}
    return {"safe": True, "leaks": []}
