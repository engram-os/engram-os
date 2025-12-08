import requests
import json

API_URL = "http://localhost:8000/search"
USER_ID = "vikram"

response = requests.get(API_URL, params={"query": "deadline", "user_id": USER_ID})
data = response.json()

print("\n RAW SERVER RESPONSE:")
print(json.dumps(data, indent=2))