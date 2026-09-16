# NetOps MCP Server

A Model Context Protocol (MCP) server providing structured, bottom-up network diagnostics (OSI Layers 1–3) for client-side environments. Bridges host network telemetry directly into LLM clients (such as Claude Desktop) via standard `stdio` transport.

## Setup & Installation
1. **Clone repository & enter environment:**
    ```bash
    git clone https://github.com/drew-1618/netops-mcp.git
    cd netops-mcp
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
2. **Run via MCP Inspector (Development):**
    ```bash
    mcp dev src/server.py
    ```
3. **Claude Desktop Integration:**
Add the following block to your `claude_desktop_config.json`:
    ```json
    "mcpServers": {
        "netops": {
        "command": "wsl.exe",
        "args": [
            "bash",
            "-c",
            "cd /absolute/path/to/netops-mcp && .venv/bin/python src/server.py"
        ]
        }
    }
    ```