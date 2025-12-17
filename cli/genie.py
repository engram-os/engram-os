import sys
import requests
import os

if len(sys.argv) < 2:
    print("No command provided.")
    sys.exit(1)

broken_command = sys.argv[1]

try:
    print(f"Genie is thinking... [{broken_command}]")
    response = requests.post(
        "http://localhost:8000/api/terminal/fix", 
        json={"command": broken_command},
        timeout=60
    )
    response.raise_for_status()
    
    fixed_command = response.json()["fixed_command"]
    
    print(f"\n✨ Suggested Fix: \033[1;32m{fixed_command}\033[0m")
    user_input = input("Run this command? [Y/n] ")
    
    if user_input.lower() in ["", "y", "yes"]:
        os.system(fixed_command)
    else:
        print("Aborted.")

except Exception as e:
    print(f"Genie is dead: {e}")