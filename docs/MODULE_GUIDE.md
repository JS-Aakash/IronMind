# IronMind Module Guide & Implementation Roadmap

## 10 Major System Modules

| Module # | Name | Directory | Primary Role |
|---|---|---|---|
| **M1** | **Web Workbench & Shell** | `apps/frontend` | Industrial dashboard with live agent visualizer and sovereignty radar. |
| **M2** | **Task Understanding & Classifier** | `services/model_gateway/router.py` | Intent extraction and required capability detection (`vision`, `coding`, `rag`, `docx`). |
| **M3** | **Capability-Based Model Router** | `services/model_gateway/router.py` | Deterministic scoring and multi-stage pipeline auto-selection (`qwen3:8b`, `qwen2.5-coder:7b`, `qwen2.5vl:7b`). |
| **M4** | **Model Manager & Local Gateway** | `services/model_gateway` | Memory-efficient loading/unloading into local VRAM via Ollama/vLLM. |
| **M5** | **Agent Orchestrator (ReAct)** | `services/agent` | State-machine lifecycle (`PLAN → EXECUTE → OBSERVE → VERIFY → ITERATE → COMPLETE`). |
| **M6** | **Controlled Tool System & Sandbox** | `services/sandbox` | Permissioned file I/O, calculations, and Docker execution (`network: none`). |
| **M7** | **Document Intelligence & OCR** | `services/document_intelligence` | Scanned PDF, handwriting, and P&ID engineering diagram parsing. |
| **M8** | **Industrial Knowledge Base (Local RAG)** | `services/rag` | Embeddings and semantic retrieval over MRPL SOPs and manuals. |
| **M9** | **Artifact Engine & Provenance** | `services/artifacts` | Real industrial deliverable generation (`.docx`, `.xlsx`, `.pptx`) with SHA-256 signatures. |
| **M10** | **Sovereignty Monitor & Security Audit** | `services/sovereignty` | Air-gap verification, 0 external calls monitor, and immutable audit trail. |
