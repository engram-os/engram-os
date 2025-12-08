# Contributing to Engram

First off, thank you for considering contributing to Engram! It's people like you that make the open-source community such an amazing place to learn, inspire, and create.

Engram is an ambitious project to build a fully local, privacy-preserving AI Operating System. We welcome contributions from engineers, designers, and thinkers who share our vision of **0% Data Egress**.

## Core Philosophy

Before you write code, please understand our core tenets. We will reject PRs that violate these:

1.  **Local-First:** All inference must happen on the user's hardware (Ollama/Llama 3). No API calls to OpenAI/Anthropic for core logic.

2.  **Privacy by Design:** User data (files, browser history, memories) must never leave the Docker container.

3.  **Transparent Action:** Agents must never take high-stakes actions (sending emails, deleting files) without user review or clear logs.

---

## The Tech Stack

We use a distributed microservices architecture. Familiarity with these tools is helpful:

* **Backend:** Python 3.11 (FastAPI, Celery, Watchdog)

* **Frontend:** TypeScript (Next.js 14, Tailwind CSS, Framer Motion)

* **Infrastructure:** Docker Compose, Redis, Qdrant (Vector DB)

* **AI:** Ollama (Llama 3.1 8B)

---

## Local Development Setup

Unlike the end-user installation (`npx engram-os`), developers should run the system from source to access logs and hot-reloading.

### Prerequisites
* [Docker Desktop](https://www.docker.com/) (Required for the Brain)

* [Node.js 18+](https://nodejs.org/) (Required for Frontend)

* Python 3.11+

### 1. Clone & Configure
```bash
git clone https://github.com/VS251/engram-os.git
cd engram-os
```

**Create the Inbox folder structure**
```bash
mkdir -p AI_Inbox/processed
```

### 2. Setup Secrets

You will need your own Google Cloud credentials for the Agents to work.

Obtain ```credentials.json``` from Google Cloud Console (Calendar + Gmail scopes).

Place it in the root directory.

Run the token generator:

```bash
pip install google-auth-oauthlib
python3 generate_token.py
```

### 3. Run the Backend 

We use the provided shell scripts to manage the Docker lifecycle.

```bash
chmod +x start_os.sh
./start_os.sh
```

This will boot the API, Worker, Database, and Dashboard.

### 4. Run the Marketing Site (Frontend)

If you are contributing to the landing page or documentation:

```bash
cd frontend
npm install
npm run dev
```

Open ```http://localhost:3000``` to view the site.

## Project Structure
```agents/:``` Python logic for autonomous workers (Calendar, Email).

```cli/:``` The Node.js installer script published to NPM.

```frontend/:``` The Next.js marketing website.

```docker-compose.yml:``` Orchestrates the local infrastructure.

```app.py:``` The Streamlit Local Dashboard (The actual product UI).

## How to Submit a Pull Request

1. Fork the repository and create your branch from ```main```.

2. Naming Convention: Use descriptive branch names (```feat/email-agent-upgrade, fix/ingestor-crash```).

3. Test your changes:
- If modifying the Backend, ensure ```docker-compose up``` builds cleanly.

- If modifying Agents, verify they appear in the "Activity Feed" on the dashboard.

4. Format your code:
- Python: We follow PEP 8.

- TypeScript: We use ESLint/Prettier.

5. Submit the PR! Please include a description of why the change is needed and screenshots if UI related.

## Reporting Bugs
If you find a bug, please create an Issue using the following template:

- OS/Hardware: (e.g. MacBook M2 Air, 16GB RAM)

- Docker Status: (Output of ```docker ps``` if relevant)

- Logs: (Relevant snippets from ```docker logs```)

- Steps to Reproduce: Clear, numbered steps.

## License
By contributing, you agree that your contributions will be licensed under the MIT License defined in the ```LICENSE``` file.
