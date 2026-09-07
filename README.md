# ⚙️ IronMind: Sovereign Industrial AI Platform
### Autonomous On-Premise Agentic AI System for Critical Process Engineering, Refining & Petrochemical Infrastructure

[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15.0+-black?style=flat&logo=next.js&logoColor=white)](https://nextjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=flat&logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Security](https://img.shields.io/badge/Air--Gap-100%25%20Zero--Egress-10B981?style=flat&logo=shield&logoColor=white)](#-data-sovereignty-air-gap-security--compliance)
[![Tests](https://img.shields.io/badge/Test%20Suite-103%20Passed%20(100%25)-brightgreen?style=flat&logo=pytest&logoColor=white)](#-automated-verification--testing)
[![Compliance](https://img.shields.io/badge/Standards-ISA--5.1%20%7C%20ISO%2013709%20%7C%20API%20610%20%7C%20ISO%2010816-blue?style=flat)](#-industrial-standards-compliance)

---

## 🏭 1. Executive & Industrial Overview

Modern process plants, petroleum refineries, and critical manufacturing facilities operate under strict regulatory and operational constraints. Plant instrumentation diagrams (P&IDs), operational setpoints, non-destructive examination (NDE) inspection records, and rotating equipment vibration measurements contain proprietary engineering intellectual property.

Transmitting plant data, equipment scans, or operating telemetry to public multi-tenant cloud AI models introduces severe risks:
1. **Intellectual Property Exposure**: Confidential refinery operating margins, proprietary fluid formulations, and equipment vulnerabilities risk exposure across external infrastructure.
2. **Regulatory Non-Compliance**: Violates industrial cybersecurity standards (**IEC 62443**, **NIS2**, **NERC CIP**) which mandate strict physical and network segregation between Industrial Control Systems (ICS) and external networks.
3. **Execution Without Physical Bounds**: Conventional cloud chatbots hallucinate calculations, do not execute unit tests in containerized sandboxes, and cannot audit or mutate multi-sheet fleet workbooks.

**IronMind** is an enterprise-grade, **100% on-premise sovereign AI platform** built specifically for heavy process industries. Running entirely on local workstation hardware or air-gapped plant servers, IronMind coordinates specialized open-weight models to parse complex engineering diagrams, retrieve standard operating procedures, self-heal code calculations in isolated process sandboxes, and produce digitally signed executive deliverables.

---

## 🏛️ 2. High-Level System Architecture

IronMind uses a decoupled, micro-service architecture designed for absolute air-gapped reliability:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                SOVEREIGN PRESENTATION TIER                               │
│  Next.js 15 (App Router) • TypeScript • Tailwind CSS • Server-Sent Events (SSE) Stream    │
│  ┌─────────────────────────┬─────────────────────────┬────────────────────────────────┐  │
│  │    Agent Workbench      │   Sovereignty Monitor   │   Cryptographic Provenance     │  │
│  │   (1-Click Evaluation)  │  (Zero-Egress Sniffer)  │   (SHA-256 Audit Inspector)    │  │
│  └─────────────────────────┴─────────────────────────┴────────────────────────────────┘  │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │ HTTP Loopback (127.0.0.1:8000) / SSE
┌────────────────────────────────────────────▼─────────────────────────────────────────────┐
│                             CORE RUNTIME & GATEWAY TIER                                  │
│  FastAPI • Unified Model Router • Dynamic Capability Allocator • Zero-Egress Firewall    │
│                                                                                          │
│  ┌────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                     Open-Weight Local Model Engine (Ollama IPC)                    │  │
│  │   • Task Router:         qwen3:0.6b     (Task classification & capability mapping) │  │
│  │   • Engineering Reasoner: qwen3:8b       (SOP reconciliation & multi-step plan)    │  │
│  │   • Code Generator:      qwen2.5-coder:7b (API 610 / ISO 13709 calculation logic)   │  │
│  │   • Vision / Multimodal: qwen2.5vl:7b    (ISA-5.1 P&ID & OCR document analysis)    │  │
│  └────────────────────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │ Internal Dispatch
┌────────────────────────────────────────────▼─────────────────────────────────────────────┐
│                          AGENT ORCHESTRATION & EXECUTION TIER                            │
│                                                                                          │
│   ┌──────────────────────────────────────────────────────────────────────────────────┐   │
│   │  ReAct Agent State Machine (Plan ➔ Route ➔ Execute ➔ Observe ➔ Verify ➔ Seal)   │   │
│   └────────────────────────────────────────┬─────────────────────────────────────────┘   │
│                                            │                                             │
│    ┌───────────────────────────────────────┴────────────────────────────────────────┐     │
│    │ Intelligent Self-Healing Retry Loop                                            │     │
│    │ Attempt 1 ➔ Sandbox Failure ➔ Error Diagnostics ➔ Code Fix ➔ Attempt 2 (✓)    │     │
│    └───────────────────────────────────────┬────────────────────────────────────────┘     │
│                                            │                                             │
│    ┌───────────────────────────────────────┼────────────────────────────────────────┐     │
│    │                                       │                                        │     │
│    ▼                                       ▼                                        ▼     │
│ ┌──────────────────────┐        ┌──────────────────────┐        ┌──────────────────────┐  │
│ │  Ephemeral Sandbox   │        │  Sovereign Local RAG │        │  Deliverable Engine  │  │
│ │  Isolated Subprocess │        │  Dense Vector Store  │        │  python-docx, xlsx,  │  │
│ │  Network: None (Air) │        │  Exact SOP Citations │        │  pptx, reportlab-pdf │  │
│ └──────────────────────┘        └──────────────────────┘        └──────────────────────┘  │
└────────────────────────────────────────────┬─────────────────────────────────────────────┘
                                             │
┌────────────────────────────────────────────▼─────────────────────────────────────────────┐
│                           STORAGE, ASSETS & PROVENANCE TIER                              │
│  • storage/uploads/   : Pre-staged plant scans, P&ID images, fleet vibration spreadsheets│
│  • storage/knowledge/ : Indexed MRPL SOPs, API standards, safety rules, vector indices   │
│  • storage/artifacts/ : Digitally verified business deliverables (.docx, .xlsx, .pptx)   │
│  • storage/audit/     : Immutable SHA-256 tamper-evident event ledger (audit_ledger)     │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 3. Specialized Model Matrix & Dual-Stage Routing

IronMind eliminates resource contention on industrial workstations by deploying task-optimized models via a dual-engine architecture:

| Operational Role | Model Tag | Architecture | Specialization in Process Engineering | Host RAM/VRAM |
| :--- | :--- | :--- | :--- | :--- |
| **Fast AI Router** | `qwen3:0.6b` | MoE Lightweight | Classifies user prompts into domains (Coding, Spreadsheet, Vision, SOP Analysis) in < 50ms. | ~800 MB |
| **Engineering Synthesis** | `qwen3:8b` | Dense Transformer | Deep reasoning over refinery SOPs, plant safety thresholds, root cause failure analysis, executive drafting. | ~5.8 GB |
| **Calculation & Coding** | `qwen2.5-coder:7b`| Code Specialist | Generates mathematically rigorous ISO 13709 / API 610 algorithms and self-testing boundary assertion suites. | ~5.5 GB |
| **Multimodal Vision** | `qwen2.5vl:7b` | Vision-Language | Analyzes high-resolution engineering schematics, extracts ISA-5.1 P&ID instrumentation tags, reads field scans. | ~6.2 GB |

### Dual-Stage Routing Logic
1. **Stage 1 (Intent & Capability Analysis)**: The lightweight router parses the query, attached file MIME types, and prompt requirements to select the primary specialist model.
2. **Stage 2 (Pipeline Sequencing)**: Multi-step industrial tasks execute sequentially. For example, a scanned inspection note first routes to `qwen2.5vl:7b` for OCR table extraction, routes SOP retrieval through the local RAG engine, and hands off to `qwen3:8b` for formal Word document authoring.

---

## 🔁 4. Intelligent Self-Healing Sandbox & Verification Loop

Industrial calculation code must never fail silently in production. When an agent generates code or runs numerical scripts, IronMind dispatches the code into an **isolated process sandbox** with network egress disabled.

```
       [ Agent Generates Solution & Assertions ]
                         │
                         ▼
             [ Sandbox Execution Mode ]
                         │
        ┌────────────────┴────────────────┐
        │                                 │
 [ Exit Code 0: Verified ✓ ]     [ Exit Code != 0: Failure ]
        │                                 │
        ▼                                 ▼
[ Seal Provenance & Deliver ]     [ Capture stdout, stderr, exit code ]
                                          │
                                          ▼
                                 [ Structured Error Analysis ]
                                 • Root Cause Diagnostics
                                 • Previous-attempt context
                                          │
                                          ▼
                                 [ Formulate Modified Solution ]
                                          │
                                          ▼
                                 [ Attempt 2 Execution ]
                                          │
                                          ▼
                                 [ Verification Passed ✓ ]
```

### Key Recovery Features:
- **Maximum 3 Retries**: Strictly bounds compute cycles and prevents circular failure loops.
- **Differential Context Injection**: The backend sends the original task, the current code, the exact exception traceback, and prior attempt summaries back to the model.
- **Visual Workbench Stepper**: The user interface renders an interactive timeline node for every attempt:  
  `Attempt 1` $\rightarrow$ `Failure (Exit 1)` $\rightarrow$ `Error Analysis` $\rightarrow$ `Fix Applied` $\rightarrow$ `Attempt 2` $\rightarrow$ `Verification (Exit 0) ✓`.
- **Safety Handoff**: If an error is unrecoverable (e.g. missing dependencies or physical boundary contradictions), the agent halts and requests human engineering intervention.

---

## 🎯 5. The 4 Flagship Production Scenarios

IronMind includes pre-staged evaluation scenarios accessible via 1-click buttons on the **Workbench (`/workbench`)**:

### Scenario 1: Autonomous Code Generation & Isolated Sandbox Verification
- **Target Standard**: **API 610 / ISO 13709** (Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries).
- **Goal**: Formulate a robust Python module to calculate centrifugal pump hydraulic power ($P_{\text{hyd}} = \frac{\rho \cdot g \cdot Q \cdot H}{1000}\text{ kW}$), accompanied by self-testing unit assertions verifying positive power for nominal flow, zero power at shutoff ($Q = 0$), and fluid density scaling.
- **Workflow**:
  1. `qwen2.5-coder:7b` formulates formula functions and automated `assert` boundary checks.
  2. The code is executed in an ephemeral process sandbox.
  3. All assertions are verified (100% pass rate, exit code 0).
  4. Delivers [`iso13709_pump_hydraulics.py`](file:///storage/artifacts/iso13709_pump_hydraulics.py) with SHA-256 cryptographic provenance.

### Scenario 2: Fleet Vibration Analysis, Excel Anomaly Formatting & Executive KPI Sheet
- **Target Standard**: **ISO 10816-3** (Mechanical Vibration Evaluation).
- **Goal**: Ingest a staged refinery workbook ([`MRPL_P101_Inspection_Data.xlsx`](file:///storage/uploads/MRPL_P101_Inspection_Data.xlsx)), evaluate multi-pump vibration velocities against the 4.5 mm/s RMS threshold, highlight abnormal assets in RED, and synthesize an executive KPI summary sheet.
- **Workflow**:
  1. Inspects raw worksheet rows and column schemas via `spreadsheet.inspect`.
  2. Modifies cells using openpyxl via `spreadsheet.modify`, calculating mean velocities and deviation percentages.
  3. Applies red fills (`#FEE2E2`) to non-compliant equipment tags (`P-101A`, `P-104B`).
  4. Appends a formatted "KPI Summary" sheet with executive benchmarks.
  5. Renders a complete **Change Summary Dashboard** showing atomic sheet mutations and computed metrics.

### Scenario 3: Multimodal Industrial Vision & ISA-5.1 P&ID Engineering Analysis
- **Target Standard**: **ISA-5.1** (Instrumentation Symbols and Identification).
- **Goal**: Inspect a high-resolution engineering P&ID drawing ([`MRPL_Crude_Distillation_P101_PID.png`](file:///storage/uploads/MRPL_Crude_Distillation_P101_PID.png)) of Crude Distillation Unit 1 (CDU-01).
- **Workflow**:
  1. `qwen2.5vl:7b` scans schematics for primary equipment, piping lines, and safety instruments.
  2. Extracts equipment tags: `P-101A/B` (Crude Charge Pumps), `T-101` (Atmospheric Distillation Tower), `E-101` (Pre-heat Exchanger Train), `V-101` (Flash Drum).
  3. Maps field transmitters (`PT-101`, `PT-102`, `FT-101`) and safety interlocks (PSV-102 thermal relief set at 16.5 bar).
  4. Outputs structured JSON asset breakdowns for maintenance management.

### Scenario 4: Scanned Plant Inspection Report $\rightarrow$ Regulatory Word Approval Note
- **Target Standard**: **MRPL SOP MECH 4.2** & **API Standard 610**.
- **Goal**: Process a degraded field inspection scan ([`MRPL_P101_Inspection_Scan.txt`](file:///storage/uploads/MRPL_P101_Inspection_Scan.txt)) for pump P-101, retrieve maintenance thresholds via local RAG, and produce an official Word document (`.docx`).
- **Workflow**:
  1. OCR extracts Drive End (DE) bearing vibration ($4.8\text{ mm/s}$ RMS) and Plan 53B seal weepage.
  2. Semantic search against the local vector database retrieves **MRPL SOP Section 4.2**, identifying that $4.8\text{ mm/s}$ exceeds the $4.5\text{ mm/s}$ overhaul trigger.
  3. `qwen3:8b` drafts an executive justification with exact SOP section citations.
  4. Synthesizes [`MRPL_Approval_Note_P_101_Sample.docx`](file:///storage/artifacts/MRPL_Approval_Note_P_101_Sample.docx) featuring official headers, justification tables, and 3-tier signature blocks.

---

## 🔒 6. Data Sovereignty, Air-Gap Security & Compliance

IronMind enforces hardware and software boundaries guaranteeing zero data egress:

### 1. Mandatory Air-Gap Guardrails
- **Hard-coded Cloud Blocker**: Any network attempt to reach external LLM endpoints (OpenAI, Anthropic, Google Cloud, Bedrock) is intercepted by `SovereigntyService` and terminated with a `SovereigntyViolationError`.
- **Loopback Socket Binding**: Backend processes (`uvicorn`, `ollama`) bind exclusively to `127.0.0.1`.

### 2. Three-Tier Measurement Telemetry
The **Sovereignty Monitor (`/sovereignty`)** displays live network telemetry across three independent verification tiers:
1. **Directly Measured**: Real-time OS packet sniffer monitoring network interfaces (`0 Bytes Egress`, `0 External Connections`, `0 Outbound DNS Queries`).
2. **Derived from Application Logs**: Cumulative count of verified on-premise model inferences, local tool calls, and containerized sandbox runs.
3. **Enforced by Configuration**: Explicit system constraints (`airgap_mode: true`, `network_mode: none`).

### 3. Cryptographic Provenance Ledger
Every operation is registered in an append-only JSONL ledger ([`audit_ledger.jsonl`](file:///storage/audit/audit_ledger.jsonl)). Each entry contains:
- `event_id`: Unique cryptographic identifier.
- `timestamp`: Host local time synchronization.
- `action` & `operator`: Attributed service or user.
- `sha256_hash`: Hash computed across event payload and chained to the previous block hash (`previous_hash`).

---

## 📂 7. Repository Structure

```text
IronMind/
├── apps/
│   ├── backend/                      # FastAPI Sovereign REST API & SSE Server
│   │   └── app/
│   │       ├── api/v1/endpoints/     # Modular route controllers
│   │       │   ├── agent.py          # Task submission & SSE streaming
│   │       │   ├── artifacts.py      # Deliverable downloads & verification
│   │       │   ├── audit.py          # Provenance ledger & event timelines
│   │       │   ├── health.py         # System health & local time sync
│   │       │   ├── knowledge.py      # Local RAG document management
│   │       │   ├── models.py         # Model status & dynamic registration
│   │       │   ├── sovereignty.py    # Zero-egress network telemetry
│   │       │   └── tools.py          # Direct tool invocation endpoints
│   │       ├── core/                 # App configuration & dependency injection
│   │       └── main.py               # Application entrypoint
│   └── frontend/                     # Next.js 15 Web Application
│       └── src/
│           ├── app/
│           │   ├── page.tsx          # Industrial command dashboard
│           │   ├── workbench/        # Interactive agent execution & retry viewer
│           │   ├── sovereignty/      # Real-time packet sniffer & air-gap proof
│           │   ├── runs/             # Historical execution traces & logs
│           │   ├── artifacts/        # Verified deliverables gallery
│           │   ├── audit/            # Cryptographic blockchain-style ledger
│           │   ├── knowledge/        # Local SOP document browser
│           │   └── models/           # Local model catalog & latency monitor
│           └── components/           # Reusable UI cards, tables, badges
├── packages/
│   └── shared/                       # Shared Pydantic models & utility helpers
├── services/                         # Isolated Core Business Services
│   ├── agent/                        # ReAct Orchestrator, Planner, Verifier & State
│   │   └── tools/                    # Sandboxed tools (doc, spreadsheet, vision, code)
│   ├── artifacts/                    # Native .docx, .xlsx, .pptx, .pdf, .py generators
│   ├── audit/                        # Cryptographic provenance service
│   ├── document_intelligence/        # Local OCR & layout parsing pipeline
│   ├── model_gateway/                # Model Router, Ollama provider, health checkers
│   ├── rag/                          # Local vector store, dense chunker, retriever
│   ├── sandbox/                      # Process-confined isolated code runner
│   └── sovereignty/                  # Interface sniffer & egress auditor
├── storage/                          # Local Storage Volumes
│   ├── artifacts/                    # Verified business deliverables & registry.json
│   ├── audit/                        # Append-only SHA-256 audit ledger
│   ├── knowledge/                    # Refinery SOPs & persistent vector index
│   ├── tasks/                        # Stored task run definitions
│   └── uploads/                      # Pre-staged engineering scans, P&ID drawings
├── scratch/                          # Operational & Maintenance Utilities
│   ├── clean_demo_storage.py         # Reset storage to pristine flagship state
│   └── reindex_clean_knowledge.py    # Re-index dense vector store
└── tests/                            # Comprehensive Automated Test Suite (103 tests)
```

---

## 🚀 8. Installation & Quickstart Guide

### Prerequisites
- **Operating System**: Linux (Ubuntu 22.04+ recommended) or Windows 10/11 with PowerShell
- **Python**: 3.10 to 3.12
- **Node.js**: 18.x or 20.x LTS
- **Ollama**: Local inference daemon ([Download Ollama](https://ollama.ai))

---

### Step 1: Pull Local Open-Weight Models
Start the Ollama service and download the required models:
```bash
# Verify daemon status
ollama list

# Pull the specialized model quartet
ollama pull qwen3:0.6b
ollama pull qwen3:8b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5vl:7b
```

---

### Step 2: Backend Setup
From the repository root:
```bash
# Create and activate virtual environment (optional)
python -m venv .venv
# On Linux/macOS: source .venv/bin/activate
# On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r apps/backend/requirements.txt

# Launch FastAPI backend server (Port 8000)
python -m uvicorn apps.backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check**: [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)

---

### Step 3: Frontend Setup
In a separate terminal:
```bash
cd apps/frontend

# Install dependencies
npm install

# Start Next.js development server (Port 3000)
npm run dev
```
- **Web Application**: [http://localhost:3000](http://localhost:3000)

---

### Step 4: Run Flagship Scenarios
1. Open [http://localhost:3000/workbench](http://localhost:3000/workbench).
2. Click any of the **1-Click Evaluation Presets** at the top of the interface:
   - `1. Code & Sandbox`: Triggers centrifugal pump hydraulic calculation and sandbox validation.
   - `2. Spreadsheet Analysis`: Ingests fleet vibration Excel sheet, applies conditional formatting, and computes KPIs.
   - `3. Multimodal Vision (P&ID)`: Ingests the CDU-01 P&ID schematic and identifies instrumentation.
   - `4. Scanned Report → Docx`: Cross-references SOP 4.2 and authors a formal approval note in Word format.
3. Monitor real-time execution in the **Activity Log** and review final deliverables in the **Artifact Preview**.

---

## 🧪 9. Automated Verification & Testing

The platform includes an extensive test suite verifying mathematical solvers, sandbox isolation, RAG semantic recall, and security boundaries.

```bash
# Run the complete test suite
pytest -v
```

### Test Suite Summary:
```text
======================= 103 passed in 118.36s =======================
```

| Test Module | Coverage Scope | Verified Properties |
| :--- | :--- | :--- |
| `test_self_repair_loop.py` | Intelligent Recovery Loop | Retries on exit code != 0, root cause analysis, fix injection, halt on unrecoverable errors. |
| `test_pid_and_network_audit.py` | P&ID & Sovereignty | ISA-5.1 tag parsing, packet audit stream generation, SHA-256 attestation signing. |
| `test_agent_tools_upgrade.py` | Tools & Spreadsheets | Openpyxl cell mutations, red anomaly formatting, KPI calculation, verifier checks. |
| `test_production_features.py` | Gateway & Registry | Dynamic model registration, model toggling, role assignment persistence. |
| `test_agent_orchestrator.py` | Agent State Machine | ReAct execution lifecycle, SSE token streaming, tool dispatch. |
| `test_rag_system.py` | Local Vector Store | Dense chunking, cosine similarity ranking, exact section citation retrieval. |
| `test_document_intelligence.py` | Document OCR | PDF text extraction, coordinate mapping, table extraction. |
| `test_artifacts_engine.py` | Deliverable Engine | Valid DOCX, XLSX, PPTX, and PDF generation with SHA-256 provenance. |
| `test_sovereignty_monitor.py` | Air-Gap Boundary | Zero-egress network assertion, Cloud provider blocking. |
| `test_audit_system.py` | Provenance Ledger | Chained block hashing, append-only JSONL persistence. |

---

## 📋 10. Industrial Standards Compliance

| Standard | Scope & Application in IronMind |
| :--- | :--- |
| **ISA-5.1** | Instrumentation Symbols and Identification used in multimodal P&ID schematic interpretation. |
| **ISO 13709 / API 610** | Centrifugal Pumps for Petroleum, Petrochemical and Natural Gas Industries calculations. |
| **ISO 10816-3** | Evaluation of machine vibration by measurements on non-rotating parts (severity zones A to D). |
| **IEC 62443** | Industrial communication networks - Network and system security (air-gap, zone segmentation). |
| **ISO/IEC 27001** | Cryptographic provenance chaining and immutable audit logging. |

---

## ⚖️ 11. License & Operational Notices

- **License**: Enterprise Sovereign Industrial License.
- **Air-Gap Guarantee**: This software does not transmit diagnostic telemetry, user inputs, or model weights outside the local host environment.
- **Hardware Sizing**: For production deployment, a minimum of 32 GB system RAM and an NVIDIA RTX 3090 / 4090 (24 GB VRAM) or Apple Silicon (36 GB+ unified memory) is recommended for concurrent local inference across the model quartet.
