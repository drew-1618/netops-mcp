import re
import subprocess
import socket
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from mcp.server.mcpserver import MCPServer

from src.db import log_incident
from src.validators import validate_target, validate_count

# initialize MCP server
mcp = MCPServer("NetOps-Server")

# locate runbooks dir relative to this script
RUNBOOKS_DIR = Path(__file__).resolve().parent.parent / "runbooks"

@mcp.tool()
def run_ping(target: str, count: int = 3) -> dict:
    """ 
    Pings an IP address or hostname to check reachability, average latency, and packet loss.
    """
    # input validation
    is_valid_target, target_err = validate_target(target)
    if not is_valid_target:
        return {"target": target, "reachable": False, "error": target_err}

    is_valid_count, count_err = validate_count(count)
    if not is_valid_count:
        return {"target": target, "reachable": False, "error": count_err}
    
    cmd = ["ping", "-c", str(count), target]
    ping_timeout = 7   # seconds timeout for ping command
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=ping_timeout)
        if res.returncode != 0:
            return {"target": target, "reachable": False, "error": res.stderr.strip()}

        # extract packet loss
        loss_match = re.search(r"(\d+)% packet loss", res.stdout)
        packet_loss = int(loss_match.group(1)) if loss_match else None

        # extract avg RTT 
        rtt_match = re.search(r"rtt min/avg/max/mdev = [\d.]+/([\d.]+)/", res.stdout)
        avg_rtt = float(rtt_match.group(1)) if rtt_match else None

        return {
            "target": target,
            "reachable": True,
            "packet_loss_percent": packet_loss,
            "average_latency_ms": avg_rtt,
        }

    except subprocess.TimeoutExpired:
        return {"target": target, "reachable": False, "error": f"Ping command timed out at {ping_timeout} seconds"}

@mcp.tool()
def get_gateway_telemetry() -> dict:
    """
    Discover the local default gateway and check first-hop reachability.
    """
    try:
        # query default gateway using Windows host routing table
        cmd = ["route.exe", "print", "0.0.0.0"]
        route_timeout = 3   # seconds timeout for route command
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=route_timeout)
        if res.returncode != 0:
            return {"found": False, "error": "route.exe execution failed"}

        # Matches lines structured like: Network Destination | Netmask | Gateway | Interface | Metric
        # Example: 0.0.0.0          0.0.0.0      192.168.1.1    192.168.1.50     35
        match = re.search(r"0\.0\.0\.0\s+0\.0\.0\.0\s+([0-9\.]+)", res.stdout)
        if not match:
            return {"found": False, "error": "No default gateway found in routing table"}

        gw_ip = match.group(1).strip()

        if gw_ip.startswith("127.") or gw_ip == "0.0.0.0":
            return {"found": False, "error": f"Invalid gateway route detected: {gw_ip}"}
        
        # ping gateway directly (2 packets for fast timeout)
        ping_res = run_ping(gw_ip, count=2)
        return {
            "gateway_ip": gw_ip,
            "first_hop_reachable": ping_res.get("reachable", False),
            "packet_loss_percent": ping_res.get("packet_loss_percent"),
            "gateway_latency_ms": ping_res.get("average_latency_ms"),
        }
    except subprocess.TimeoutExpired:
        return {"found": False, "error": f"Gateway query timed out at {route_timeout} seconds"}
    except Exception as e:
        return {"found": False, "error": str(e)}

@mcp.tool()
def get_wifi_telemetry() -> dict:
    """
    Gathers local WiFi interface telemetry such as SSID, signal strength percentage,
    radio type, and link rates.
    """
    cmd = ["netsh.exe", "wlan", "show", "interfaces"]
    wifi_timeout = 5   # seconds timeout for WiFi telemetry command

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=wifi_timeout)
        output = res.stdout

        if res.returncode != 0:
            return {"connected": False, "error": output.strip()}

        # check if interface is disconnected
        state_match = re.search(r"^\s*State\s*:\s*(.+)$", output, re.MULTILINE)
        state = state_match.group(1).strip() if state_match else "unknown"
        if "connected" not in state.lower():
            return {"connected": False, "state": state}

        # extract metrics with regex
        ssid_match = re.search(r"^\s*SSID\s*:\s*(.+)$", output, re.MULTILINE)
        signal_match = re.search(r"^\s*Signal\s*:\s*(\d+)%", output, re.MULTILINE)
        radio_match = re.search(r"^\s*Radio type\s*:\s*(.+)$", output, re.MULTILINE)
        rx_match = re.search(r"^\s*Receive rate \(Mbps\)\s*:\s*([\d.]+)", output, re.MULTILINE)
        tx_match = re.search(r"^\s*Transmit rate \(Mbps\)\s*:\s*([\d.]+)", output, re.MULTILINE)

        return {
            "connected": True,
            "ssid": ssid_match.group(1).strip() if ssid_match else None,
            "signal_percent": int(signal_match.group(1)) if signal_match else None,
            "radio_type": radio_match.group(1).strip() if radio_match else None,
            "rx_rate_mbps": float(rx_match.group(1)) if rx_match else None,
            "tx_rate_mbps": float(tx_match.group(1)) if tx_match else None,
        }

    except subprocess.TimeoutExpired:
        return {"connected": False, "error": f"netsh command timed out at {wifi_timeout} seconds"}

@mcp.tool()
def resolve_dns(hostname: str) -> Dict[str, Any]:
    """
    Resolves a hostname using the local system resolver & measures resolution latency
    """

    is_valid, error_msg = validate_target(hostname)
    if not is_valid:
        return {
            "status": "failed",
            "hostname": hostname,
            "latency_ms": 0.0,
            "error": error_msg,
            "resolved_ips": [],
        }

    target = hostname.strip()
    start_time = time.perf_counter()
    try:
        # resolve IPv4/IPv6 addresses
        address_info = socket.getaddrinfo(target, None)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # deduplicate resolved IP addresses
        resolved_ips = list({entry[4][0] for entry in address_info})

        return {
            "status": "success",
            "hostname": target,
            "latency_ms": elapsed_ms,
            "resolved_ips": resolved_ips,
            "record_count": len(resolved_ips)
        }
    except socket.gaierror as e:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return {
            "status": "failed",
            "hostname": target,
            "latency_ms": elapsed_ms,
            "error": str(e),
            "resolved_ips": []
        }

@mcp.tool()
def create_incident_ticket(
    target: str,
    failing_layer: str,
    summary: str,
    severity: str = "medium"
) -> Dict[str, Any]:
    """
    Creates a structured operational incident ticket payload for escalation
    """

    ticket_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
    timestamp = datetime.now(timezone.utc).isoformat()

    ticket_payload = {
        "ticket_id": ticket_id,
        "created_at_utc": timestamp,
        "status": "OPEN",
        "severity": severity.lower(),
        "target": target,
        "failing_layer": failing_layer,
        "summary": summary,
    }

    # persist locally
    try:
        log_incident(ticket_payload)
    except Exception as e:
        # don't crash MCP response if disk logging as an issue
        return {
            "status": "warning",
            "message": f"Ticket generated but persistence failed: {e}",
            "ticket": ticket_payload,
        }
    return {
        "status": "created",
        "message": f"Incident ticket {ticket_id} opened and logged successfully",
        "ticket": ticket_payload,
    }
    
    
@mcp.resource("netops://runbooks/network-triage")
def get_network_triage_runbook() -> str:
    """
    Exposes standard-backed network triage guidelines as a runbook resource.
    """
    doc_path = RUNBOOKS_DIR / "network_triage_guide.md"
    if not doc_path.exists():
        return f"Error: Runbook not found at {doc_path}"
    return doc_path.read_text(encoding="utf-8")

@mcp.prompt()
def triage_network(target_host: str = "8.8.8.8") -> str:
    """
    Guides the agent through a disciplined, bottom-up Layer 1-3 network diagnostic sequence
    """

    return f"""
    You are a Tier-2/3 Network Operations Center (NOC) diagnostics agent.
    A connectivity incident has been reported for target destination: '{target_host}'.

    Execute the following systematic, bottom-up triage workflow:

    1. Operational Standards Ingestion:
       - Read the reference runbook at 'netops://runbooks/network-triage' to establish SLA baselines for RSSI, packet loss, RTT, and DNS latency.

    2. Layer 1/2 (Physical & Data Link Check):
       - Query Wi-Fi telemetry and interface statistics.
       - Evaluate signal strength (RSSI), link rates, and radio status against runbook thresholds.

    3. Layer 3 (LAN / First-Hop Gateway Check):
       - Call the `get_gateway_telemetry` tool to discover and verify first-hop reachability.
       - Fault Isolation: If L1/2 is healthy but gateway latency exceeds threshold (>10-20 ms) or drops packets, isolate fault domain to Local LAN / Router.

    4. Application / Service Layer (DNS Resolution):
       - If '{target_host}' is a domain name, execute DNS resolution.
       - Fault Isolation: If the query fails (NXDOMAIN/timeout) or latency exceeds 150 ms, isolate fault domain to DNS / Resolver.

    5. Layer 3 (WAN / Upstream Reachability Check):
       - Ping target '{target_host}' to evaluate end-to-end packet loss and latency.
       - Fault Isolation: If the gateway is clean but '{target_host}' fails, isolate fault domain to Upstream WAN / External Routing.

    6. Synthesis & Incident Escalation:
       - Present a structured summary: Link Status, Fault Domain (Local Wi-Fi, LAN Gateway, DNS, or WAN), and Metric Violations.
       - If an SLA violation or outage is confirmed, call 'create_incident_ticket' with the target, failing layer, and diagnostic summary.
       - If all checks pass within thresholds, provide recommendations without opening a ticket.
    """

@mcp.tool()
def lookup_remediation(category: str) -> dict:
    """
    Look up specific remediation advice and thresholds from the triage runbook.
    
    Valid categories: 'physical' (or 'signal', 'L1'), 'packet_loss' (or 'loss'), 'latency' (or 'RTT', 'bufferbload').
    """
    doc_path = RUNBOOKS_DIR / "network_triage_guide.md"
    if not doc_path.exists():
        return {"error": f"Runbook missing at {doc_path}"}

    content = doc_path.read_text(encoding="utf-8")

    # map common query terms to section header keywords
    category_map = {
        "physical": "Physical Layer",
        "signal": "Physical Layer",
        "l1": "Physical Layer",
        "packet_loss": "Packet Loss",
        "loss": "Packet Loss",
        "latency": "Latency",
        "rtt": "Latency",
        "bufferbloat": "Latency",
        "dns": "DNS",
        "resolution": "DNS",
        "nameserver": "DNS",
    }

    target_keyword = category_map.get(category.lower().strip())
    if not target_keyword:
        return {
            "found": False,
            "error": (
                f"Invalid category '{category}'. Valid options:"
                f" {list(category_map.keys())}"
            ),
        }

    # extract the targeted section up to the next ## heading or EOF
    pattern = rf"(## [^\n]*{re.escape(target_keyword)}[^\n]*\n[\s\S]*?)(?=\n## |\Z)"
    match = re.search(pattern, content, re.IGNORECASE)

    if match:
        return {
            "found": True,
            "category": category,
            "section_content": match.group(1).strip(),
        }
    return {
        "found": False,
        "error": f"Could not locate runbook section for '{category}' in '{doc_path}'"
    }


# transport entry point
if __name__ == "__main__":
    mcp.run(transport="stdio")