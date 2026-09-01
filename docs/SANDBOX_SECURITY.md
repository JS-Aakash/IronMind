# 🔒 IronMind Python Code Sandbox: Security Architecture & Isolation Model

## 1. Executive Overview
The **IronMind Sovereign Python Sandbox** provides an air-gapped containerized compute runtime specifically designed for AI-generated code. It guarantees that generated scripts and unit tests cannot tamper with the host operating system, exfiltrate refinery telemetry, consume unbounded hardware resources, or escape the designated ephemeral workspace.

---

## 2. Core Security Pillars

```
                     ┌────────────────────────────────────┐
                     │   AI CODING AGENT (Qwen2.5-Coder)  │
                     └─────────────────┬──────────────────┘
                                       │ (Generated Script & Tests)
                                       ▼
                     ┌────────────────────────────────────┐
                     │   LAYER 1: AST SECURITY FIREWALL   │
                     │  • Scans for forbidden imports     │
                     │  • Blocks host path traversals     │
                     │  • Blocks socket/HTTP patterns     │
                     └─────────────────┬──────────────────┘
                                       │ (Verified Safe Code)
                                       ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │             LAYER 2: DOCKER CONTAINER HARDWARE ISOLATION               │
   │                                                                        │
   │   • Network Mode: NONE (--network none)                                │
   │   • Memory Limit: 256MB Hard Cap (--memory 256m)                       │
   │   • CPU Limit: 1.0 Core (--cpus 1.0)                                   │
   │   • Process Limit: 64 PIDs (--pids-limit 64)                           │
   │   • Root Filesystem: Read-Only (--read-only)                           │
   │   • Workspace: Ephemeral tmp mount (/workspace:rw)                     │
   │   • Timeout: 15s Hard Process Termination Timer                        │
   │                                                                        │
   │   ┌──────────────────────────────────────────────────────────────┐     │
   │   │                  ISOLATED PYTHON INTERPRETER                 │     │
   │   │    • main.py execution                                       │     │
   │   │    • pytest test suite assertions                            │     │
   │   └──────────────────────────────────────────────────────────────┘     │
   └───────────────────────────────────┬────────────────────────────────────┘
                                       │
                                       ▼
                     ┌────────────────────────────────────┐
                     │     LAYER 3: AUTOMATIC CLEANUP     │
                     │  • Disk workspace unlinked         │
                     │  • Memory buffers deallocated      │
                     │  • SHA-256 Event Audit Recorded    │
                     └────────────────────────────────────┘
```

---

## 3. Defense Mechanisms & Threat Matrix

| Threat / Attack Vector | Mitigation Strategy | Enforced By |
|---|---|---|
| **Data Exfiltration / Cloud Egress** | Zero-network container isolation (`--network none`) and AST blocking of `socket`, `urllib`, `requests`, `httpx`. | Docker Engine & Static Scanner |
| **Host Filesystem Tampering** | Host filesystem is never mounted. Only a dedicated scratch directory (`/workspace`) is mapped. Root is `--read-only`. | Linux Cgroups / Container Isolation |
| **Path Traversal Attacks** | Rejection of paths containing `../`, `/etc/shadow`, `C:\Windows`, `.env`. | AST Scanner & Storage Whitelist |
| **Runaway Infinite Loops** | Execution timeout (15s default) triggering hard `SIGKILL` on the container or child process. | Asyncio Subprocess Watchdog |
| **Fork Bombs / Resource Exhaustion** | Strict memory caps (`--memory 256m`) and process caps (`--pids-limit 64`). | Linux Cgroups |
| **Subshell & Privilege Escalation** | Direct binary invocation with no `/bin/sh` wrapper; AST blocks `subprocess.Popen`, `os.system`, `pty`. | Static AST Filter & Non-root User |

---

## 4. Structured Result Schema

Every execution returns a strictly validated JSON payload:

```json
{
  "status": "success",
  "stdout": "Pump P-101 Hydraulic Efficiency: 78.4%",
  "stderr": "",
  "exit_code": 0,
  "duration_ms": 342.5,
  "tests": [
    {
      "name": "test_hydraulic_efficiency_api610",
      "status": "passed",
      "duration_ms": 12.1,
      "message": null
    }
  ],
  "memory_limit_mb": 256,
  "cpu_limit": 1.0,
  "network_mode": "none",
  "execution_engine": "docker_container",
  "cleanup_verified": true
}
```

---

## 5. Ephemeral Lifecycle & Audit Trail

1. **Workspace Provisioning**: A unique directory `/tmp/ironmind_sandbox_<uuid>` is generated.
2. **Execution**: Code runs inside container with CPU, Memory, and Timeout boundaries.
3. **Observation**: `stdout`, `stderr`, and `pytest` test results are collected.
4. **Guaranteed Cleanup**: The temporary workspace directory is immediately destroyed in a `finally` block.
5. **Sovereignty Audit**: An immutable event record is dispatched to the Sovereignty Service audit log with duration and exit code.
