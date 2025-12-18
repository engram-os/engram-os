from fastapi import APIRouter
from pydantic import BaseModel
from ollama import Client

router = APIRouter()

client = Client(host='http://host.docker.internal:11434')

class CodeRequest(BaseModel):
    code: str
    instruction: str = "Explain this code"

@router.post("/api/spectre/chat")
async def spectre_chat(request: CodeRequest):
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
        response = client.chat(model='llama3.1', messages=[
            {'role': 'user', 'content': prompt}
        ])
        return {"response": response['message']['content']}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}