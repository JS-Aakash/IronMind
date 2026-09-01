# IronMind Architecture Blueprint

## Overview
**IronMind** is a sovereign, on-premise agentic AI workbench built for **Mangalore Refinery and Petrochemicals Limited (MRPL)** and PSU industrial environments. It enables automated execution of confidential knowledge work without transmitting sensitive organizational data to external cloud AI providers.

```
                              ┌──────────────────────────────────────────────┐
                              │            IRONMIND WEB WORKBENCH            │
                              │           (Next.js App Router UI)            │
                              └──────────────────────┬───────────────────────┘
                                                     │ REST / SSE
                                                     ▼
                              ┌──────────────────────────────────────────────┐
                              │          FASTAPI API GATEWAY (v1)            │
                              └──────────────────────┬───────────────────────┘
                                                     │
                                 ┌───────────────────┴───────────────────┐
                                 ▼                                       ▼
                     ┌───────────────────────┐               ┌───────────────────────┐
                     │  TASK CLASSIFIER &    │               │  SOVEREIGNTY MONITOR  │
                     │  CAPABILITY ROUTER    │               │  & AUDIT SUBSYSTEM    │
                     └───────────┬───────────┘               │ (0-Egress, Live Packets)
                                 │                           └───────────────────────┘
          ┌──────────────────────┼──────────────────────┐
          ▼                      ▼                      ▼
┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
│ REASONING MODEL   │  │   VISION MODEL    │  │   CODING MODEL    │
│ (Qwen3 / Ollama)  │  │ (Qwen2.5-VL/OCR)  │  │ (Qwen2.5-Coder)   │
└─────────┬─────────┘  └─────────┬─────────┘  └─────────┬─────────┘
          │                      │                      │
          └──────────────────────┼──────────────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │ AGENT ORCHESTRATOR    │
                     │ Plan → Exec → Verify  │
                     └───────────┬───────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         ▼                       ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   LOCAL RAG     │     │   LOCAL TOOLS   │     │ ISOLATED CODE   │
│ (Chroma/BGE-M3) │     │ (Docx/Xlsx/Pptx)│     │ SANDBOX (Docker)│
│ SOPs & Manuals  │     │ Calc/File Tools │     │ Safe Execution  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 ▼
                     ┌───────────────────────┐
                     │ ARTIFACT ENGINE &     │
                     │ PROVENANCE TRACKER    │
                     │ (Verified Deliverables│
                     └───────────────────────┘
```

## Directory Structure
```
IronMind/
├── apps/
│   ├── backend/        # FastAPI Application
│   └── frontend/       # Next.js 15 TypeScript Dashboard
├── services/
│   ├── model_gateway/          # Model registry, memory management & routing
│   ├── agent/                  # Multi-step ReAct state machine
│   ├── rag/                    # Local embeddings & vector search
│   ├── document_intelligence/  # Local OCR & P&ID diagram parsing
│   ├── sandbox/                # Isolated code execution
│   ├── artifacts/              # Formatted deliverables (DOCX/XLSX/PPTX)
│   └── sovereignty/            # 0-egress network verification & audit trail
├── packages/
│   └── shared/         # Data contracts, schemas & enums
├── storage/
│   ├── uploads/        # Ingested inspection scans & P&IDs
│   ├── knowledge/      # Local SOPs & equipment manuals
│   ├── artifacts/      # Generated business deliverables
│   └── temp/           # Temporary execution scratchpad
├── tests/              # Pytest suite
└── docs/               # Architecture & operational guides
```
