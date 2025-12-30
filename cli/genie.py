import sys
import requests
import os

if len(sys.argv) < 2:
    print("No command provided.")
    sys.exit(1)

history_blob = sys.argv[1]

candidates = history_blob.split('\n')

broken_command = None

for cmd in reversed(candidates):
    cmd = cmd.strip()
    if not cmd or cmd in ["??", "echo ??", "clear"]:
        continue

    broken_command = cmd
    break

    if not broken_command:
        print("Could not find a valid broken command in recent history.")
        sys.exit(1)    

if len(sys.argv) > 1 and sys.argv[1] == "help":
    print("Usage: Type '??' after a failed command to fix it.")
    sys.exit(0)

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