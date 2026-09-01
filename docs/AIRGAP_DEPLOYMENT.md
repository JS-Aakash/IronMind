# 🛡️ IronMind Air-Gapped & Sovereign Network Deployment Guide

This document specifies the technical architecture, monitoring boundaries, and deployment configurations for operating the **IronMind SovereignAI Workbench** in strictly air-gapped, zero-egress industrial environments (e.g., Oil Refineries, Power Plants, Defense facilities).

---

## 1. Metric Classification & Measurement Integrity

To prevent misleading or ambiguous telemetry, IronMind strictly separates its sovereignty telemetry into three auditable categories:

| Category | Description | Metrics Tracked | Verification Mechanism |
| :--- | :--- | :--- | :--- |
| **Directly Measured** | Real-time byte and packet counts observed on network sockets and application interceptors. | • `socket_egress_bytes` (0)<br>• `external_http_attempts_intercepted`<br>• `dns_queries_attempted` (0)<br>• `loopback_probes_verified` | Low-level OS socket binding monitor and HTTP transport interceptor. |
| **Derived from Logs** | Aggregated counts parsed from internal task execution and tool invocation ledgers. | • `local_model_calls`<br>• `local_tool_executions`<br>• `sandbox_executions`<br>• `cloud_llm_calls` (0)<br>• `external_api_calls` (0) | `storage/audit/audit_ledger.jsonl` event ledger. |
| **Enforced by Config** | Invariant architectural constraints guaranteed by software guardrails and container sandboxing. | • `network_mode: none`<br>• `cloud_providers_blocked: true`<br>• `airgap_mode: true`<br>• `allowed_hosts: [127.0.0.1, localhost]` | `CloudProviderBlocker` & Docker engine flags. |

---

## 2. Structured Sovereignty Status (`GET /api/v1/sovereignty/status`)

```json
{
  "mode": "air_gapped",
  "internet_access": "blocked",
  "external_api_calls": 0,
  "cloud_llm_calls": 0,
  "local_model_calls": 18,
  "data_egress_bytes": 0,
  "measurement_breakdown": {
    "directly_measured": {
      "socket_egress_bytes": 0,
      "external_http_attempts_intercepted": 0,
      "dns_queries_attempted": 0,
      "loopback_probes_verified": 1
    },
    "derived_from_application_logs": {
      "local_model_calls": 18,
      "local_tool_executions": 7,
      "sandbox_executions": 3,
      "cloud_llm_calls": 0,
      "external_api_calls": 0
    },
    "enforced_by_configuration": {
      "network_mode": "none (Docker sandbox) / 127.0.0.1 loopback binding only",
      "cloud_providers_blocked": true,
      "airgap_mode": true,
      "allowed_hosts": ["127.0.0.1", "localhost", "::1"]
    }
  },
  "last_verified_at": "2026-09-01T06:55:00.000000"
}
```

---

## 3. Disabling Outbound Network Access in Production

### A. Docker Air-Gap Deployment (`docker-compose.airgap.yml`)

Configure an internal Docker network with zero gateway routing:

```yaml
version: '3.8'

networks:
  sovereign_internal:
    driver: bridge
    internal: true # Disables default gateway and blocks all outbound external traffic

services:
  ollama:
    image: ollama/ollama:latest
    networks:
      - sovereign_internal
    volumes:
      - ./storage/models:/root/.ollama
    ports:
      - "127.0.0.1:11434:11434"

  backend:
    build:
      context: .
      dockerfile: apps/backend/Dockerfile
    networks:
      - sovereign_internal
    environment:
      - AIRGAP_MODE=true
      - OLLAMA_BASE_URL=http://ollama:11434
    ports:
      - "127.0.0.1:8000:8000"
    depends_on:
      - ollama
```

### B. Linux Host Firewall (`iptables`)

To strictly lock down the host machine running IronMind:

```bash
# 1. Allow local loopback interface
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# 2. Allow established internal subnet connections
iptables -A OUTPUT -d 10.0.0.0/8 -j ACCEPT

# 3. Block all other outbound public internet connections
iptables -A OUTPUT -j DROP
```

### C. Windows Host Firewall (`PowerShell`)

```powershell
# Block all outbound traffic from the Python runtime except local loopback
New-NetFirewallRule -DisplayName "IronMind Block All Outbound" `
    -Direction Outbound `
    -Program "C:\Users\jsaak\AppData\Local\Programs\Python\Python312\python.exe" `
    -Action Block `
    -RemoteAddress 1.0.0.0-255.255.255.255
```

---

## 4. Application-Level Cloud Provider Guardrails

The application includes `CloudProviderBlocker` in [`services/sovereignty/guardrails.py`](file:///c:/Users/jsaak/OneDrive/Desktop/Coding/IronMind/services/sovereignty/guardrails.py). If any configuration or user tries to pass cloud API keys (e.g. `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, `AWS_SECRET_ACCESS_KEY`), the server immediately rejects execution and raises `SovereigntyViolationError`.
