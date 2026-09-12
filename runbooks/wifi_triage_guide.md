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