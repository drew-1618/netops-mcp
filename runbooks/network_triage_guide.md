# Wi-Fi Quality of Experience (QoE) Triage Runbook

## 1. Physical Layer (L1/L2): Signal Attenuation
- **Metric**: RSSI (dBm) / Signal Percentage
- **Standard Reference**: CWNP Design Standards / Cisco Voice over WLAN Baseline
- **Healthy**: RSSI >= -67 dBm (Signal >= 70%)
- **Degraded**: RSSI < -70 dBm (Signal < 50%)
- **Impact**: Radio steps down to low-order modulation (MCS index), increasing airtime consumption and latency.
- **Remediation**:
  - Relocate client closer to the access point.
  - Mitigate physical obstacles (walls, metal surfaces).
  - If distance is unavoidable, evaluate 2.4 GHz band for better wall penetration.

## 2. Network Layer (L3): Packet Loss
- **Metric**: Loss Percentage
- **Standard Reference**: RFC 2680 (One-Way Packet Loss Metric) / ITU-T G.114
- **Healthy**: 0% loss
- **Degraded**: > 1% loss
- **Impact**: TCP retransmissions, jitter buffer underruns, degraded voice/video calling.
- **Remediation**:
  - Inspect for local co-channel interference (switch AP from congested 2.4/5 GHz channel).
  - Check physical Ethernet backhaul cabling to the router.

## 3. Network Layer (L3): Latency & Bufferbloat
- **Metric**: Round Trip Time (RTT in ms)
- **Standard Reference**: ITU-T Y.1541 (Class 1 QoS Metrics)
- **Healthy**: Gateway RTT < 20 ms, DNS RTT < 50 ms
- **Degraded**: Gateway RTT > 80 ms
- **Impact**: High round-trip time, interactive lag, slow connection handshakes.
- **Remediation**:
  - Check for local bandwidth saturation (large downloads, heavy backups).
  - Restart local residential gateway/modem to clear buffer queues.

## 4. Application / Network Service Layer: DNS Resolution
- **Metric**: Lookup Latency (ms) / Query Success State
- **Standard Reference**: RFC 1035 (Domain Names) / IETF RFC 8484
- **Healthy**: Resolution latency < 50 ms; returns valid A/AAAA records (0% error).
- **Degraded**: Latency > 150 ms (slow resolver responses, recursive query timeouts).
- **Failed**: `NXDOMAIN`, `gaierror` (lookup failure), or query timeouts.
- **Impact**: Web pages stall during initial connection handshakes, services appear completely unreachable even if raw IP reachability (ICMP) is healthy.
- **Remediation**:
  - Test external fallback resolvers (e.g., `1.1.1.1` or `8.8.8.8`) to isolate local vs. upstream DNS outages.
  - Flush the local OS resolver cache (`ipconfig /flushdns` or `systemd-resolve --flush-caches`).
  - Verify DHCP-assigned nameservers on the gateway or interface.

## Response Formatting Contract
Whenever conducting a triage workflow, you MUST format your final response using the following exact structure every time. Do not omit the table or substitute conversational paragraphs for standard layers:
### 1. Telemetry Summary
| Layer | Metric / Probe | Status | Details |
| :--- | :--- | :--- | :--- |
| L1/L2 Physical/Link | Wi-Fi Signal / Link Speed | PASS / FAIL / DEGRADED | ... |
| L3 LAN Gateway | Ping Default Gateway | PASS / FAIL | ... |
| L7 DNS Resolution | Local Resolver Lookup | PASS / FAIL | ... |
| L3 WAN Transport | Target ICMP Reachability | PASS / FAIL / SKIPPED | ... |

### 2. Fault Domain Isolation
- **Isolated Layer:** [Physical | LAN Gateway | DNS | WAN Transport | None]
- **Target Classification:** [Routable Public | RFC Reserved / Documentation | Private LAN]
- **Root Cause Analysis:** Concise, 1-2 sentence technical summary.

### 3. Operational Action
- **Incident Escalation:** [None Required | Ticket Created: INC-XXXXX | Operator Confirmation Required]
- **Recommended Remediation:** Bulleted runbook steps.

Do not omit the table or substitute bulleted narrative for standard layers.
