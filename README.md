# NetOps MCP Server

A Model Context Protocol (MCP) server providing structured, bottom-up network diagnostics (OSI Layers 1–3) for LLM clients like Claude Desktop. 

---

## Key Highlights

- **WSL2 Host Boundary Traversal**: WSL2 runs inside a virtualized Hyper-V switch. Standard Linux utilities cannot see host Wi-Fi or physical adapters. This server bridges across the boundary into Windows host binaries (`netsh.exe`, `route.exe`) to collect physical Wi-Fi signal, link rates, and default gateway status.
- **Complete MCP Primitive Coverage**:
  - **Tools**: Active diagnostic probes (`run_ping`, `get_gateway_telemetry`, `get_wifi_telemetry`, `resolve_dns`, `lookup_remediation`, `create_incident_ticket`).
  - **Resources**: Exposes standard-backed runbooks (`netops://runbooks/network-triage`) directly into the agent's context window.
  - **Prompts**: `triage_network` guides the LLM through a disciplined, bottom-up diagnostic sequence rather than jumping to conclusions.
- **Defensive Engineering**:
  - Strict input validation against command chaining (`;`, `|`, `&`, etc.) and option-injection flags (`-`).
  - Hard timeouts on all subprocess network calls (`ping`, `netsh`, `route`).
  - SQLite persistence for tracking triage incidents locally without crashing server responses on I/O failures.

---

## Setup & Installation

### Prerequisites
- Python `>= 3.10`
- [`uv`](https://github.com/astral-sh/uv) (recommended) or standard `python3 -m venv`

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/drew-1618/netops-mcp.git
cd netops-mcp

# Using uv (fast, deterministic sync from uv.lock)
uv sync
```

### 2. Run Directly or with MCP Inspector

Test the server in stdio mode:
```bash
uv run python -m src.server
```

Or test interactively using the official MCP Inspector:
```bash
npx @modelcontextprotocol/inspector uv run python -m src.server
```

---

## Claude Desktop Integration (Windows + WSL)

Add the server to your Claude Desktop configuration file (`%APPDATA%\Claude\claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "netops": {
      "command": "wsl.exe",
      "args": [
        "-e",
        "/<your-absolute-path>/netops-mcp/.venv/bin/python",
        "-m",
        "src.server"
      ]
    }
  }
}
```

> **Note**: Claude Desktop will automatically launch and manage the background WSL process over `stdio`. No terminal or WSL window needs to remain open.

---

## MCP Reference

### Tools
| Tool | Arguments | Description |
| :--- | :--- | :--- |
| `run_ping` | `target: str`, `count: int = 3` | Measures reachability, packet loss %, and average RTT latency. |
| `get_gateway_telemetry` | _None_ | Queries host routing table for default gateway and tests first-hop reachability. |
| `get_wifi_telemetry` | _None_ | Extracts host Wi-Fi interface state, SSID, signal %, and link rates via `netsh.exe`. |
| `resolve_dns` | `hostname: str` | Resolves hostnames via local resolver and measures DNS resolution latency in ms. |
| `lookup_remediation` | `category: str` | Extracts specific runbook remediation sections (`physical`, `packet_loss`, `latency`, `dns`). |
| `create_incident_ticket`| `target`, `failing_layer`, `summary`, `severity` | Generates a unique incident ID (`INC-XXXXXXXX`) and records it in SQLite. |

### Resources
| URI | Description |
| :--- | :--- |
| `netops://runbooks/network-triage` | Full operational SLA thresholds and bottom-up triage guidelines from `runbooks/network_triage_guide.md`. |

### Prompts
| Prompt | Arguments | Description |
| :--- | :--- | :--- |
| `triage_network` | `target_host: str = "8.8.8.8"` | Guides the LLM step-by-step through Layer 1 to Layer 3 diagnostic checks and incident escalation. |