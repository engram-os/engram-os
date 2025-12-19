# Engram OS

> **Your AI, On Your Device. Complete Privacy. Complete Control.**

[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![Llama 3.1](https://img.shields.io/badge/Model-Llama_3.1-purple.svg)](https://ollama.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

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
🧞 Genie is thinking...
✨ Suggested Fix: git status
Run this command? [Y/n]
```

**Engram Spectre (VS Code Extension)**
- A privacy-first AI pair programmer that lives in your editor.

- Trigger: Command Palette (```Spectre: Ask```).

- Logic: Reads your currently selected code and sends it to the local Engram API (Docker).

- Action: Explains logic, finds bugs, or refactors code without data ever leaving your machine.

## Usage Guide
**The Dashboard**

Once started, the dashboard opens at ```http://localhost:8501```.
- Chat: Interact with your long-term memory.

- Activity: View a real-time feed of Agent decisions (Thinking, Tool Use, Errors).

- Settings: Manage API connections and manual overrides.

**Ingesting Data**
- Files: Drop any ```.pdf```, ```.txt```, or ```.md``` file into the ```AI_Inbox``` folder on your desktop. It will be instantly consumed by the OS.

- Thoughts: Type commands directly into the Chat interface (e.g., "Remind me to call Mom").

## Manual Development Setup
If you prefer to run from source without ```npx```:

**1. Clone the Repo:**

```bash
git clone https://github.com/VS251/engram-os.git
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
