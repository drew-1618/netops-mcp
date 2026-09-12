# NetOps MCP Server

A Model Context Protocol (MCP) server providing structured, bottom-up network diagnostics (OSI Layers 1–3) for client-side environments. Bridges host network telemetry directly into LLM clients (such as Claude Desktop) via standard `stdio` transport.

## Architecture

```text
 Claude Desktop (Host)
       │
       ▼ (stdio via WSL bridge)
 MCP Runtime (server.py)
   ├── Tools:
   │    ├── get_wifi_telemetry (L1/L2 via netsh.exe)
   │    ├── run_ping           (L3 RTT & packet loss)
   │    └── lookup_remediation (Runbook query engine)
   ├── Resources:
   │    └── netops://runbooks/wifi-triage (Standards-backed runbook)
   └── Prompts:
        └── triage_network     (Automated bottom-up diagnostic agent)
```

## Setup & Installation
1. Clone repository & enter environment:
    ```bash
    git clone 
    cd netops-mcp
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
2. Run via MCP Inspector (Development):
    ```bash
    mcp dev src/server.py
    ```
3. Claude Desktop Integration:
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