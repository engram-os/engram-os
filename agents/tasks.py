import os
import re
import json
import logging
import requests
from core.worker import celery_app
from qdrant_client import QdrantClient
from qdrant_client.http import models
from agents.tools import add_calendar_event
from agents.logger import log_agent_action
from agents.gmail_tools import fetch_unread_emails, create_draft_reply
from core.identity import get_or_create_identity

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
COLLECTION_NAME = "second_brain"
LOCAL_USER_ID = get_or_create_identity()["user_id"]

qdrant = QdrantClient(host=QDRANT_HOST, port=6333)
logger = logging.getLogger(__name__)

@celery_app.task(name="agents.tasks.run_email_agent")
def run_email_agent():
    log_agent_action("EmailAgent", "WAKE_UP", "Checking Inbox for unread messages...")

    # 1. Reading
    emails = fetch_unread_emails(limit=5)
    if not emails:
        log_agent_action("EmailAgent", "READ", "Inbox Zero (or no new unread).")
        return

    log_agent_action("EmailAgent", "READ", f"Found {len(emails)} unread emails.")

    # 2. Thinking (In loop)
    for email in emails:
        if "noreply" in email['sender'] or "newsletter" in email['sender']:
            continue
            
        system_prompt = """
        You are an executive email assistant.
        Analyze the incoming email.

        GOAL:
        - If it needs a reply, draft a polite, professional, and concise response.
        - If it is spam/notification, return action: "ignore".

        RULES:
        1. Direct Question/Task -> "draft_reply"
        2. FYI / Updates -> "draft_reply" (Polite ack)
        3. Ambiguous -> "draft_reply" (Clarification)
        4. Spam -> "ignore"
        
        Format:
        {
            "action": "draft_reply" or "ignore",
            "reply_text": "The full body of the email reply..."
        }
        """
        
        user_content = f"From: {email['sender']}\nSubject: {email['subject']}\nBody: {email['body']}"

        payload = {
            "model": "llama3.1:latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "format": "json",
            "stream": False
        }
        
        try:
            response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=(5, 60)).json()
            decision = json.loads(response['message']['content'])

            if decision.get("action") == "draft_reply":
               # 3. Action
                log_agent_action("EmailAgent", "DECISION", f"Drafting reply to {email['sender']}")
                create_draft_reply(email['id'], decision['reply_text'])
                log_agent_action("EmailAgent", "TOOL_USE", f"Saved Draft: Re: {email['subject']}")
                
        except Exception as e:
            log_agent_action("EmailAgent", "ERROR", f"Failed on {email['id']}: {e}")
            
    return {"status": "done"}

@celery_app.task(name="agents.tasks.test_agent_pulse")
def test_agent_pulse(data):
    logger.info(f"[AGENT LOG] Pulse received. Processing data: {data}")
    return {"status": "alive"}

@celery_app.task(name="agents.tasks.run_calendar_agent")
def run_calendar_agent():
    log_agent_action("CalendarAgent", "WAKE_UP", "Agent started scheduled check.")

    try:
        recs = qdrant.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="user_id",
                        match=models.MatchValue(value=LOCAL_USER_ID)
                    )
                ],
                must_not=[
                    models.FieldCondition(
                        key="status",
                        match=models.MatchValue(value="processed")
                    )
                ]
            ),
            limit=20,
            with_payload=True
        )[0]
    except Exception as e:
        log_agent_action("CalendarAgent", "ERROR", f"Qdrant Read Error: {e}")
        return

    if not recs:
        return

    active_memories = []
    id_map = {}
    
    for r in recs:
        if r.payload.get("status") == "processed":
            continue
            
        content = r.payload.get('memory') or r.payload.get('text') or r.payload.get('data')
        if content:
            id_key = str(r.id)
            id_map[id_key] = r.id
            active_memories.append(f"[ID: {r.id}] {content}")
            
    if not active_memories:
        return

    memory_text = "\n".join(active_memories)
    log_agent_action("CalendarAgent", "READ", f"Analyzed {len(active_memories)} pending items.")

    system_prompt = """
    You are an intelligent scheduling assistant. 
    Analyze the pending memories. 
    
    GOAL: Only schedule events if the user EXPLICITLY requests it (e.g. "Schedule a meeting", "Remind me to", "Book a slot").
    
    RULES:
    1. IGNORE general facts. (e.g. "The project launches in December" is a fact, NOT a meeting request).
    2. IGNORE file content unless it contains a clear task for you.
    3. IF a request is found, extract the real topic and time.
    4. Do NOT use generic titles.
    5. You MUST include the 'memory_id' from the input.
    
    Format:
    {
        "action": "schedule", 
        "title": "Topic", 
        "time": "Time", 
        "description": "Context", 
        "memory_id": "ID"
    }
    
    If no explicit request is found, return: {"action": "none"}
    """

    payload = {
        "model": "llama3.1:latest",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Pending Items:\n{memory_text}"}
        ],
        "format": "json",
        "stream": False
    }

    try:
        response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=(5, 60)).json()
        content = response['message']['content']
        decision = json.loads(content)
        
        action = decision.get('action')
        log_agent_action("CalendarAgent", "DECISION", f"AI decided to: {action}")

        # 3. Action
        if action == "schedule":
            # Scheduling the event
            log_agent_action("CalendarAgent", "TOOL_USE", f"Scheduled: {decision.get('title')}") 
            add_calendar_event(
                title=decision.get("title"),
                time=decision.get("time"),
                description=decision.get("description")
            )
            
            # B. Marking done (The Fix for Loops)
            raw_id = str(decision.get("memory_id")).strip()
            uuid_match = re.search(
                r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                raw_id, re.IGNORECASE
            )
            normalized_id = uuid_match.group(0) if uuid_match else raw_id
            real_id = id_map.get(normalized_id)

            if real_id:
                # Updating the database entry to say "status: processed"
                qdrant.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload={"status": "processed"},
                    points=[real_id],
                    wait=True
                )
                log_agent_action("CalendarAgent", "UPDATE", f"Success: Marked {real_id} as processed.")
            else:
                log_agent_action("CalendarAgent", "WARNING", f"Could not find ID '{raw_id}' in map. Update failed.")
            
            return {"status": "scheduled", "details": decision}
            
    except Exception as e:
        log_agent_action("CalendarAgent", "ERROR", f"Crash: {e}")
        return {"status": "error"}
    
    return {"status": "done", "action": "none"}