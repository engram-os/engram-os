# Engram Spectre

**Spectre** is a local-first AI pair programmer for VS Code. It connects to your local Engram OS to analyze, refactor, and explain code without sending a single byte of data to the cloud.

## Features

* **Analyze Selection:** Highlight any code block and ask Spectre to explain the logic.
* **Privacy First:** All processing happens on your machine via Docker and Llama 3.
* **Fast & Offline:** Works without an internet connection (once models are downloaded).

## Requirements

This extension requires the **Engram OS Backend** to be running locally.
1.  Ensure Docker is running.
2.  Start Engram: `./start_os.sh`
3.  Ensure Ollama is accessible at `host.docker.internal`.

## Usage

1.  Select a block of code in your editor.
2.  Open the Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`).
3.  Type `Spectre: Ask` and press Enter.
4.  Type your instruction (e.g., "Find the bug in this logic").

---

**Enjoy your private AI assistant.**