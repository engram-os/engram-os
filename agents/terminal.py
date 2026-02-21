import asyncio
import os
from fastapi import APIRouter
from pydantic import BaseModel
from ollama import Client

router = APIRouter()

client = Client(host=os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434"))

class TerminalRequest(BaseModel):
    command: str

@router.post("/api/terminal/fix")  
async def fix_terminal_command(request: TerminalRequest):
    print(f"Genie received: {request.command}")
    
    prompt = f"""
    You are a ZSH/Bash terminal expert. 
    The user tried to run this command but it failed:
    "{request.command}"
    
    Fix the syntax, typo, or logic error.
    Output ONLY the corrected command string. Do not add markdown, quotes, or explanations.
    """
    
    try:
        response = await asyncio.to_thread(client.chat, model='llama3.1:latest', messages=[
            {'role': 'user', 'content': prompt}
        ])
        
        fixed_command = response['message']['content'].strip()
        fixed_command = fixed_command.replace('`', '').strip()
        
        return {"fixed_command": fixed_command}
        
    except Exception as e:
        print(f"Genie Error: {e}")
        return {"fixed_command": request.command}