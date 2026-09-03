# 🛡️ SovereignAI Workbench (IronMind)

> **Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs for Confidential Industrial Work**  
> **Problem Statement**: SIH 26117 — Mangalore Refinery and Petrochemicals Limited (MRPL)

---

## 🏛️ Executive Summary

**SovereignAI Workbench** is a production-grade, air-gapped agentic AI platform designed for confidential industrial operations in refineries and petrochemical complexes. It operates **100% on-premise** without transmitting prompts, embeddings, scanned files, or telemetry to external cloud AI providers.

---

## 🤖 Local Model Matrix & AI Task Routing

The system employs a multi-model architecture where an AI router delegates tasks to specialized open-weight models:

| Role | Model | Primary Capabilities | Context Window |
| :--- | :--- | :--- | :--- |
| **Task Router** | `qwen3:0.6b` | Rapid natural-language task classification, capability mapping, single specialist model selection | 4K |
| **Reasoning Engine** | `qwen3:8b` | Multi-step planning, engineering synthesis, SOP reconciliation, approval drafting | 32K |
| **Coding Specialist** | `qwen2.5-coder:7b` | Python calculation generation, unit test assertion formulation, bug debugging | 32K |
| **Vision / Multimodal** | `qwen2.5vl:7b` | Scanned PDF OCR, inspection photograph review, P&ID diagram symbol detection | 16K |

### Model Gateway Routing Pipeline:
```text
USER REQUEST
   │
   ▼
Task Preprocessing
   │
   ▼
qwen3:0.6b AI Router (Returns structured JSON decision)
   │
   ▼
Primary Specialist Model Selection
   ├── qwen3:8b (General Reasoning & SOP Synthesis)
   ├── qwen2.5-coder:7b (Python Calculation & Test Formulation)
   └── qwen2.5vl:7b (Scanned Reports, P&ID Diagrams, OCR)
   │
   ▼
ReAct Agent Orchestrator (PLAN → EXECUTE → OBSERVE → VERIFY → COMPLETE)
```

---

## 🏗️ Core Subsystems

```text
IronMind/
├── apps/
│   ├── frontend/             # Next.js 15 App Router, TypeScript, Tailwind CSS
│   └── backend/              # FastAPI v1 REST API & Server-Sent Events (SSE)
├── services/
│   ├── model_gateway/        # Replaceable provider abstraction (Ollama/vLLM/Mock)
│   ├── agent/                # Multi-step state machine with ToolRegistry & Verifier
│   ├── rag/                  # Local dense vector store (BGE-M3 embeddings, cosine similarity)
│   ├── document_intelligence/# Local OCR abstraction, layout preservation, coordinate mapping
│   ├── sandbox/              # Docker / Process sandbox (network_mode: none, memory/CPU limits)
│   ├── artifacts/            # DOCX/XLSX/PPTX deliverable generator (python-docx, openpyxl)
│   ├── audit/                # Cryptographic task provenance ledger (SHA-256 signatures)
│   └── sovereignty/          # 3-Tier measurement telemetry (0-egress verification)
├── storage/
│   ├── uploads/              # Ingested confidential scans & drawings
│   ├── knowledge/            # Local SOP knowledge base (MRPL-SOP-MECH-4.2)
│   ├── artifacts/            # Verified generated business deliverables
│   └── audit/                # Immutable event streams
└── tests/                    # 82 automated pytest unit and integration tests
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- **Python**: 3.10+ (Python 3.12 recommended)
- **Node.js**: 18+ (Node 20 or 24 recommended)
- **Ollama**: Local model daemon (`ollama serve`)

### 2. Check & Pull Local Models
```bash
# Verify running Ollama instance
ollama list

# Pull required local open-weight models
ollama pull qwen3:0.6b
ollama pull qwen3:8b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5vl:7b
```

### 3. Backend Setup
```bash
# Install Python dependencies
python -m pip install -r apps/backend/requirements.txt

# Start FastAPI backend (port 8000)
python -m uvicorn apps.backend.app.main:app --host 127.0.0.1 --port 8000 --reload --reload-dir apps/backend --reload-dir services --reload-dir packages
```
- API Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/health`

### 4. Frontend Setup
```bash
cd apps/frontend
npm install
npm run dev
```
- Web Workbench: `http://localhost:3000`

---

## 🎯 3 Flagship Demonstration Workflows

### 1. Industrial Inspection → Approval Note (DOCX)
- **Input**: Scanned inspection report (`MRPL_P101_Inspection_Scan.txt` / PDF)
- **Prompt**: `"Analyze this inspection report, identify the key findings, refer to the applicable maintenance SOP, and prepare an approval note."`
- **Execution Flow**:
  1. `qwen3:0.6b` classifies request into `DOCUMENT_ANALYSIS` & selects `qwen2.5vl:7b`.
  2. `document.ocr_parse` extracts vibration readings ($4.8\text{ mm/s}$ RMS) and primary seal weepage.
  3. `knowledge.search` retrieves **MRPL SOP Section 4.2** ($4.5\text{ mm/s}$ limit).
  4. `qwen3:8b` reasons that vibration exceeds ISO 10816 Zone B baseline and drafts 8 required sections.
  5. `DocxApprovalNoteGenerator` creates a genuine Microsoft Word `.docx` file with MRPL header tables, risk justifications, and 3-tier signature blocks.
  6. Deliverable is saved to `storage/artifacts/` with SHA-256 cryptographic signature.

### 2. Autonomous Coding Agent (Sandbox Verification)
- **Prompt**: `"Write Python code to calculate pump efficiency from the provided parameters. Create test cases and verify the implementation."`
- **Execution Flow**:
  1. `qwen3:0.6b` classifies request into `CODING` & selects `qwen2.5-coder:7b`.
  2. `qwen2.5-coder:7b` formulates hydraulic equations ($P = \rho \cdot g \cdot Q \cdot H$) and unit test assertions.
  3. AST engine extracts clean code and dispatches to air-gapped sandbox (`network_mode: none`).
  4. Sandbox executes code, verifies exit code 0, and captures stdout (`Pump Efficiency: 0.98%`).
  5. `AgentVerifier` confirms test passing status before marking verified.
  6. Saves deliverable as `verified_script.py` with cryptographic hash.

### 3. Multimodal P&ID Diagram Analysis
- **Input**: Piping & Instrumentation Diagram (`pid_diagram.png`)
- **Prompt**: `"Analyze this P&ID diagram, extract instrument tags and transmitters, and summarize fluid routing."`
- **Execution Flow**:
  1. `qwen2.5vl:7b` visually inspects schematics, detecting PT-101, FT-101, PSV-102.
  2. Synthesizes equipment dependencies and plant safety interlocks.

---

## 🔒 Sovereignty, Security & Zero Cloud Dependency

The Sovereignty subsystem enforces:
1. **Cloud Provider Blocker**: Hardened runtime guardrail rejecting any attempt to configure OpenAI, Anthropic, Gemini, or Bedrock endpoints with `SovereigntyViolationError`.
2. **Network Egress Interceptor**: Blocks non-loopback HTTP/TCP connections.
3. **Three-Tier Telemetry**:
   - **Directly Measured**: Socket egress bytes (`0 Bytes`), intercepted outbound requests (`0`), DNS queries (`0`).
   - **Derived from Logs**: Local model calls, sandbox runs, artifact signatures.
   - **Enforced by Configuration**: `network_mode: none`, `airgap_mode: true`.

---

## 🧪 Comprehensive Automated Test Suite

Run the full pytest suite (82 passing tests):
```bash
python -m pytest tests/ -v
```

```text
===================== 82 passed in 50.85s ======================
```
- `test_model_router.py`: Router classification & single specialist selection
- `test_agent_orchestrator.py`: ReAct state machine & tool execution
- `test_rag_system.py`: Dense chunking, embedding, and citation search
- `test_document_intelligence.py`: Local OCR & coordinate extraction
- `test_sandbox.py`: Isolated container execution & security barriers
- `test_artifacts_engine.py`: DOCX, XLSX, PPTX, PDF generation
- `test_sovereignty_monitor.py`: Air-gap verification & cloud blocking
- `test_audit_system.py`: Task provenance & event timeline
