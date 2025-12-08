import requests

API_URL = "http://localhost:8000/add-memory"
USER_ID = "vikram"

facts = [
    "Fact: My project deadline is next Friday for the UI project.",
    "Fact: I need to buy milk and coffee beans."
]

print("🚀 Starting Migration to 'second_brain'...")

for fact in facts:
    print(f"   -> Writing: {fact}")
    try:
        requests.post(API_URL, json={"text": fact, "user_id": USER_ID})
    except Exception as e:
        print(f"Error: {e}")

print("Migration Complete! All memories are now in one place.")