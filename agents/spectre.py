import asyncio
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from core.auth import get_current_user
from core.network_gateway import gateway
from core.user_registry import User

router = APIRouter()

class CodeRequest(BaseModel):
    code: str = Field(..., min_length=1, max_length=50_000)
    instruction: str = Field(default="Explain this code", max_length=2_000)

@router.post("/api/spectre/chat")
async def spectre_chat(request: CodeRequest, _: User = Depends(get_current_user)):
    print(f"Reading code...")

    prompt = f"""
    You are an expert Senior Software Engineer.

    USER INSTRUCTION: {request.instruction}

    CODE CONTEXT:
    ```
    {request.code}
    ```

    Provide a concise, technical response. If sending code back, just send the code block.
    """

    try:
        res = await asyncio.to_thread(
            gateway.post, "ollama", "/api/chat",
            json={"model": "llama3.1:latest", "messages": [{"role": "user", "content": prompt}], "stream": False},
            timeout=60,
        )
        return {"response": res.json()["message"]["content"]}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
