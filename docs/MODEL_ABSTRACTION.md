# Local Model Gateway & Abstraction Layer

## 1. Overview
The **Local Model Gateway** provides a unified, provider-agnostic abstraction over open-weight Large Language Models (LLMs) and Multimodal models. 

Application layers (Agents, RAG, Tool System, Document Intelligence) interact exclusively with `ModelService`, ensuring:
- **Zero Direct Dependencies on Ollama**: Code never calls `ollama.chat` or hardcoded URLs directly.
- **Hot-Swappable Providers**: Future providers like `vLLM`, `llama.cpp`, or `TensorRT-LLM` can be plugged in without changing higher-level agent logic.
- **Guaranteed Air-Gap & Zero Egress**: All inference remains strictly on localhost (`127.0.0.1:11434`), blocking all external internet connections.

---

## 2. Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                 AGENT / APPLICATION LAYER                   │
│        (Task Planner, RAG Retriever, Sandbox Verifier)      │
└──────────────────────────────┬──────────────────────────────┘
                               │ Calls methods on
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                        MODEL SERVICE                        │
│ (generate_text, generate_structured, analyze_image, stream) │
└──────────────┬───────────────────────────────┬──────────────┘
               │ Resolves                      │ Dispatches to
               ▼                               ▼
┌──────────────────────────────┐ ┌─────────────────────────────┐
│        MODEL REGISTRY        │ │       MODEL PROVIDER        │
│  - qwen3:8b (Reasoning)      │ │      (Abstract Base)        │
│  - qwen2.5-coder:7b (Code)   │ └──────────────┬──────────────┘
│  - qwen2.5vl:7b (Vision)     │                │
└──────────────────────────────┘                ├───────────────────────────┐
                                                ▼                           ▼
                                ┌───────────────────────────────┐ ┌───────────────────┐
                                │        OLLAMA PROVIDER        │ │   MOCK PROVIDER   │
                                │   (http://127.0.0.1:11434)    │ │   (Unit Tests)    │
                                └───────────────┬───────────────┘ └───────────────────┘
                                                │ Local Sockets Only
                                                ▼
                                ┌───────────────────────────────┐
                                │     LOCAL OPEN-WEIGHT LLMS    │
                                └───────────────────────────────┘
```

---

## 3. Supported Model Lineup

| Model ID | Functional Role | Capabilities | Primary Use Case |
|---|---|---|---|
| `qwen3:8b` | **Reasoning & Planning** | `reasoning`, `multi_step_planning`, `tool_calling` | Deconstructing user tasks, synthesizing SOP findings, drafting approval notes. |
| `qwen2.5-coder:7b` | **Coding & Verification** | `python`, `unit_testing`, `debugging`, `formulas` | Writing pump efficiency scripts, verifying API 610 boundary equations in sandbox. |
| `qwen2.5vl:7b` | **Multimodal Vision** | `vision`, `pid_diagram_parsing`, `scanned_pdf_ocr` | Inspecting P&ID engineering diagrams, scanned pressure vessel inspection logs. |

---

## 4. API Endpoints

### 1. List Models
```http
GET /api/v1/models
```

### 2. Model Health & Readiness
```http
GET /api/v1/models/{name}/health
```

### 3. Unified Inference (Text / JSON / Multimodal)
```http
POST /api/v1/models/{name}/generate
Content-Type: application/json

{
  "prompt": "Analyze vibration reading of 4.8 mm/s on Pump P-101",
  "temperature": 0.2,
  "max_tokens": 1024,
  "json_format": false
}
```

### 4. Streaming Token Emission (SSE)
```http
POST /api/v1/models/{name}/stream
Content-Type: application/json

{
  "prompt": "Generate step-by-step startup procedure for CDU-1"
}
```

### 5. Quick Verification Endpoint
```http
POST /api/v1/models/test-qwen3?prompt=Explain+centrifugal+pump+cavitation
```

---

## 5. How to Run and Test

### A. Run Backend
```bash
python -m uvicorn apps.backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

### B. Run Frontend
```bash
cd apps/frontend
npm run dev
```
- Dashboard & Model Registry UI: `http://localhost:3000/models`

### C. Run Test Suite
```bash
python -m pytest tests/ -v
```

### D. Using with Real Local Ollama Models
If you have Ollama installed on your machine:
```bash
# 1. Start Ollama
ollama serve

# 2. Pull the required models
ollama pull qwen2.5:7b
ollama pull qwen2.5-coder:7b
ollama pull qwen2.5-vl:7b
```
The application will automatically connect to `http://127.0.0.1:11434` without modifying any backend code.
