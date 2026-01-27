import os
import requests
import re

TOOLS_DIR = "tools"
API_URL = "http://localhost:8000/chat"

SYSTEM_PROMPT = """
You are a Senior Python Engineer. 
Your goal is to write a standalone Python script (a 'Tool') to fulfill a user's request.

RULES:
1. The code must be clean, heavily commented, and use standard libraries where possible.
2. If external libraries (like 'requests') are needed, import them (assume they are installed or the user will install them).
3. The script MUST have a `main()` function or a `run()` function so it can be tested immediately.
4. RETURN ONLY THE CODE. No markdown backticks, no conversational filler.
"""

def create_new_skill(user_request):
    print(f"🔨 The Tool Smith is forging a new skill: '{user_request}'...")
    
    prompt = f"Write a Python script to: {user_request}. Save it as a tool."
    
    payload = {
        "text": prompt,
        "system_prompt": SYSTEM_PROMPT, 
        "user_id": "tool_smith"
    }
    
    try:
        res = requests.post(API_URL, json=payload).json()
        code = res['reply']
        
        code = re.sub(r'^```python\n', '', code)
        code = re.sub(r'^```\n', '', code)
        code = re.sub(r'\n```$', '', code)
        
        filename = f"generated_tool_{user_request.split()[0].lower()}.py"
        filepath = os.path.join(TOOLS_DIR, filename)
        
        with open(filepath, "w") as f:
            f.write(code)
            
        return f"Success! Created {filename}.\n Run it with: python3 {filepath}"
        
    except Exception as e:
        return f"Forge Failed: {e}"

if __name__ == "__main__":
    req = input("What tool should I build? > ")
    print(create_new_skill(req))