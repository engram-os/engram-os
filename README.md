# Engram OS

> **Your AI, On Your Device. Complete Privacy. Complete Control.**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Llama 3.1](https://img.shields.io/badge/Model-Llama_3.1-purple.svg)](https://ollama.com/)
[![License: AGPL](https://img.shields.io/badge/License-AGPL-yellow.svg)](https://opensource.org/license/agpl-v3)

**Engram OS** is a local-first, event-driven AI Operating System designed to turn your personal data into autonomous action. Unlike cloud-based assistants, Engram runs entirely on your hardware using Docker, ensuring 0% data egress.

It features a dual-pipeline RAG memory system, a background nervous system for autonomous agents, and real-time sensors for file and browser activity.

---

## Quick Start

Get up and running in one command. No complex setup required.

**Prerequisites:**
* [Node.js](https://nodejs.org/) (v18 or higher)
* [Python](https://www.python.org/) (v3.10 or higher)
* [Git](https://git-scm.com/)

**Run the Installer:**
```bash
npx engram-os@latest
```
This command will:
1. Download the Engram Core.
2. Set up the local Python environment.
3. Launch the Brain (FastAPI) and the Dashboard (Streamlit).
4. Automatically open your browser to ```http://localhost:8501```.

## System Architecture
Engram is built as a distributed microservices architecture orchestrated via Docker Compose.

![](screenshots/licensed-image.jpeg)

**1. The Brain (Core)**
- LLM: Llama 3.1 (via Ollama) running locally.

- Memory: Qdrant (Vector DB) for semantic search.

- Orchestrator: FastAPI Python Backend.

**2. The Nervous System (Agents)**
- Broker: Redis (Message Queue).

- Workers: Celery (Task Execution).

- Scheduler: Celery Beat (Heartbeat).

**3. The Sensors (Inputs)**
- Ingestor: A background daemon that watches the ```AI_Inbox folder``` for PDF/TXT files, vectorizes them, and moves them to ```processed```.

- Browser Spy: A script that snapshots Chrome/Brave history for context-aware answers.

## Autonomous Agents
Engram moves beyond "Chat" by employing active agents that run on a schedule.

**The Calendar Agent**
- Trigger: Runs every 15 minutes.

- Logic: Scans short-term memory for unstructured intent (e.g., "Need to meet Dave next Tuesday").

- Action: Uses the Google Calendar API to authentically schedule events.

- Safety: Marks memories as "Processed" to prevent duplicate bookings.

**The Deep Work Email Agent**
- Trigger: Runs hourly.

- Logic: Connects to Gmail via OAuth. Filters newsletters and spam.

- Action: Drafts polite, context-aware replies to urgent emails and saves them to Drafts for human review.

**Terminal Genie**
- Engram lives in your shell. When a command fails, just ask the Genie.

- Usage:
Type `??` after any failed command to get an instant fix suggestion from Llama 3.

```bash
$ git statsu
git: 'statsu' is not a git command.
$ ??
Genie is thinking...
Suggested Fix: git status
Run this command? [Y/n]
```

**Engram Spectre (VS Code Extension)**
- A privacy-first AI pair programmer that lives in your editor.

- Trigger: Command Palette (```Spectre: Ask```).

- Logic: Reads your currently selected code and sends it to the local Engram API (Docker).

- Action: Explains logic, finds bugs, or refactors code without data ever leaving your machine.

**Local Git Agent**
- An autonomous worker that manages your version control workflow directly from the CLI.

- Trigger: Manual aliases (`g-commit`, `g-pr`, `g-check`).

- Logic: Analyses `git diff` using Llama 3 to understand code changes.

- Capabilities:
    - Auto-Commit: Generates semantic, conventional commit messages.
    - Writes structured Pull Request descriptions summarizing changes.
    - Security Sentinel: Pre-flight scans for leaked secrets (AWS keys, tokens) before pushing.

**Usage:**
```bash
$ g-commit
Engram is reading your changes...
Suggested Commit Message:
feat: Add validation logic to user signup flow
```

***Knowledge Base (Doc-Spider)***
- Turns Engram into a domain expert by ingesting external documentation.

- Trigger: Frontend UI (`/knowledge`) or API (`POST /api/docs/ingest`).

- Logic:
    - Crawl: A recursive spider (`systems/crawler.py`) navigates documentation sites.
    - Parse: Intelligently separates code blocks from prose using BeautifulSoup.
    - Vectorize: Embeds content locally using `all-MiniLM-L6-v2` and stores it in **ChromaDB**.
    - Retrieve: Uses RAG (Retrieval-Augmented Generation) to ground Llama 3's answers in the actual docs.

**Usage:**
1. Go to the Knowledge page.
2. Paste a URL (e.g., `https://flask.palletsprojects.com/`).
3. Engram scrapes the site and builds a persistent local index.
4. Ask: *"How do I write a route in Flask?"* -> Returns exact code from the docs.

![](screenshots/Doc-spider.png)

**Daily Briefing & Sync**
- Engram acts as your "Morning Mission Control," aggregating tasks from your project management tools into a prioritized executive summary.

- Unified Inbox: Normalizes issues from **Linear** and **Jira** into a single, clutter-free stream.
- AI Executive Summary: Llama 3 reads your open tickets and generates a natural language briefing (e.g., *"You have 3 critical bugs today, focused on the Auth API"*).
- Live Mission Board: A dedicated dashboard widget with live status tracking and direct links to original tickets.

**Configuration:**
Add your credentials to `.env` to activate the sync:
```
# Project Management Integrations
LINEAR_KEY=lin_api_...
JIRA_URL=[https://company.atlassian.net](https://company.atlassian.net)
JIRA_EMAIL=me@company.com
JIRA_TOKEN=ATATT3...
```

## Usage Guide
**The Dashboard**

Once started, the dashboard opens at ```http://localhost:8501```.
- Chat: Interact with your long-term memory.

- Activity: View a real-time feed of Agent decisions (Thinking, Tool Use, Errors).

- Settings: Manage API connections and manual overrides.

**Ingesting Data**
- Files: Drop any ```.pdf```, ```.txt```, or ```.md``` file into the ```AI_Inbox``` folder on your desktop. It will be instantly consumed by the OS.

- Thoughts: Type commands directly into the Chat interface (e.g., "Remind me to call Mom").

### Manual Development Setup
If you prefer to run from source without ```npx```:

**1. Clone the Repo:**

```bash
git clone https://github.com/engram-os/engram-os.git
cd engram-os
```

**2. Install Dependencies:**

```bash
pip install -r requirements.txt
```

**3. Launch:**

```bash
chmod +x start_os.sh
./start_os.sh
```

## Privacy & Security
- **Local Inference:** All thinking is done on your CPU/GPU via Llama 3.1. No text is ever sent to OpenAI or Anthropic.

- **Local Storage:** Your Vector Database (Qdrant) lives in a Docker Volume on your machine.

- **Direct API:** Google Integrations use your own personal OAuth credentials.

## Contributing
We welcome contributions! Please see [```CONTRIBUTING.md```](CONTRIBUTING.md) for details on how to set up the dev environment.

## License
This project is licensed under the AGPL-3.0 License - see the [LICENSE](LICENSE) file for details.
