import asyncio
import json
import logging
import re
from typing import Any, Dict, List, Optional, Set

import httpx

from packages.shared.models.enums import ArtifactType, ModelRole, TaskType
from services.model_gateway.models import ModelDefinition
from services.model_gateway.registry import ModelRegistry
from services.model_gateway.router_models import (
    CapabilityAnalysis,
    ModelScore,
    RoutingDecision,
    RoutingRequest,
    StageRouting,
)

logger = logging.getLogger(__name__)


class ModelRouter:
    """Lightweight AI router using local qwen3:0.6b via Ollama with robust fallback."""

    ROUTER_MODEL = "qwen3:0.6b"
    OLLAMA_BASE_URL = "http://127.0.0.1:11434"

    SYSTEM_PROMPT = """You are the IronMind Sovereign AI Classifier for an on-premise industrial refinery workbench.
Classify the user's task and select the best specialized local model.

STRICT Model Assignment Rules:
1. "qwen2.5-coder:7b" (Role: Python Coding & Sandbox)
   - MANDATORY for: writing Python code, scripts, pytest unit tests, code debugging, sandbox execution.
   - Task Types: "coding"

2. "qwen2.5vl:7b" (Role: Vision & Multimodal)
   - MANDATORY for: scanned documents, PDFs, images, OCR, P&ID engineering diagrams, blueprints, drawings.
   - Task Types: "document_analysis", "multimodal_pid"

3. "qwen3:8b" (Role: Industrial Reasoning & Planning)
   - MANDATORY for: executive planning, SOP synthesis, approval note drafting, compliance review, general engineering reasoning.
   - Task Types: "approval_note_generation", "general_reasoning", "engineering_calc"

You MUST return ONLY valid JSON in this exact format:
{
  "task_type": "coding" | "document_analysis" | "multimodal_pid" | "approval_note_generation" | "engineering_calc" | "general_reasoning",
  "primary_model": "qwen2.5-coder:7b" | "qwen2.5vl:7b" | "qwen3:8b",
  "requires_vision": true/false,
  "requires_coding": true/false,
  "requires_sandbox": true/false,
  "requires_rag": true/false,
  "target_artifact": "docx" | "xlsx" | "python" | null,
  "stage_models": { "vision": "qwen2.5vl:7b", "reasoning": "qwen3:8b", "coding": "qwen2.5-coder:7b" },
  "routing_reason": "Brief 1-sentence reason why this model was chosen"
}"""

    # Domain keywords for fallback heuristic
    VISION_KEYWORDS = {
        "scan", "scanned", "ocr", "image", "drawing", "diagram", "p&id", "pid",
        "blueprint", "photo", "photograph", "chart", "visual", "schematic", "pdf",
        "handwritten", "inspection report", "gauge", "transmitter", "valve drawing"
    }

    CODING_KEYWORDS = {
        "code", "python", "script", "program", "function", "class", "debug",
        "test", "unit test", "pytest", "sandbox", "algorithm", "efficiency calculation",
        "simulate", "execute", "benchmark", "syntax", "refactor", "api 610 calculation"
    }

    REASONING_KEYWORDS = {
        "analyze", "evaluate", "plan", "reason", "synthesize", "review",
        "approval note", "justify", "recommend", "risk assessment", "root cause",
        "compliance", "investigate", "compare", "draft", "summary", "explain"
    }

    RAG_KEYWORDS = {
        "sop", "manual", "standard", "procedure", "operating procedure",
        "guideline", "policy", "api 510", "api 610", "oims", "past correspondence",
        "specification", "reference document"
    }

    def __init__(self, registry: Optional[ModelRegistry] = None, base_url: Optional[str] = None):
        self.registry = registry or ModelRegistry()
        self.base_url = base_url or self.OLLAMA_BASE_URL

    def _get_system_prompt(self) -> str:
        coding_m = self.registry.get_model_for_role(ModelRole.CODING)
        vision_m = self.registry.get_model_for_role(ModelRole.VISION)
        reasoning_m = self.registry.get_model_for_role(ModelRole.REASONING)
        return f"""You are the IronMind Sovereign AI Classifier for an on-premise industrial refinery workbench.
Classify the user's task and select the best specialized local model.

STRICT Model Assignment Rules:
1. "{coding_m}" (Role: Python Coding & Sandbox)
   - MANDATORY for: writing Python code, scripts, pytest unit tests, code debugging, sandbox execution.
   - Task Types: "coding"

2. "{vision_m}" (Role: Vision & Multimodal)
   - MANDATORY for: scanned documents, PDFs, images, OCR, P&ID engineering diagrams, blueprints, drawings.
   - Task Types: "document_analysis", "multimodal_pid"

3. "{reasoning_m}" (Role: Industrial Reasoning & Planning)
   - MANDATORY for: executive planning, SOP synthesis, approval note drafting, compliance review, general engineering reasoning.
   - Task Types: "approval_note_generation", "general_reasoning", "engineering_calc"

You MUST return ONLY valid JSON in this exact format:
{{
  "task_type": "coding" | "document_analysis" | "multimodal_pid" | "approval_note_generation" | "engineering_calc" | "general_reasoning",
  "primary_model": "{coding_m}" | "{vision_m}" | "{reasoning_m}",
  "requires_vision": true/false,
  "requires_coding": true/false,
  "requires_sandbox": true/false,
  "requires_rag": true/false,
  "target_artifact": "docx" | "xlsx" | "python" | null,
  "stage_models": {{ "vision": "{vision_m}", "reasoning": "{reasoning_m}", "coding": "{coding_m}" }},
  "routing_reason": "Brief 1-sentence reason why this model was chosen"
}}"""

    async def _classify_with_qwen_async(self, request: RoutingRequest) -> Optional[Dict[str, Any]]:
        """Query local router model via Ollama API for fast JSON classification."""
        router_model = self.registry.get_model_for_role(ModelRole.ROUTING)
        url = f"{self.base_url}/api/generate"
        user_prompt = f"Goal: {request.goal}\nAttached Files: {request.attached_files}\nContext: {request.context}"

        payload = {
            "model": router_model,
            "system": self._get_system_prompt(),
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 350,
            },
        }

        try:
            async with httpx.AsyncClient(timeout=4.0) as client:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data.get("response", "")
                    if raw_text.strip():
                        # Extract JSON object
                        parsed = self._extract_json(raw_text)
                        if parsed and "primary_model" in parsed:
                            logger.info("AI router (%s) selected: %s", router_model, parsed.get("primary_model"))
                            return parsed
        except Exception as e:
            logger.debug("AI router (%s) call skipped (falling back): %s", router_model, str(e))

        return None

    def _classify_with_qwen_sync(self, request: RoutingRequest) -> Optional[Dict[str, Any]]:
        """Synchronous wrapper for AI router classifier."""
        router_model = self.registry.get_model_for_role(ModelRole.ROUTING)
        url = f"{self.base_url}/api/generate"
        user_prompt = f"Goal: {request.goal}\nAttached Files: {request.attached_files}\nContext: {request.context}"

        payload = {
            "model": router_model,
            "system": self._get_system_prompt(),
            "prompt": user_prompt,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": 350,
            },
        }

        try:
            with httpx.Client(timeout=3.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    raw_text = data.get("response", "")
                    if raw_text.strip():
                        parsed = self._extract_json(raw_text)
                        if parsed and "primary_model" in parsed:
                            return parsed
        except Exception as e:
            logger.debug("AI router (%s) sync call skipped (falling back): %s", router_model, str(e))

        return None

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract structured JSON from model generation string."""
        text = text.strip()
        try:
            return json.loads(text)
        except Exception:
            pass

        # Try regex block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return None

    def _extract_tokens(self, text: str) -> Set[str]:
        cleaned = re.sub(r"[^a-zA-Z0-9_\-\s]", " ", text.lower())
        tokens = set(cleaned.split())
        words = cleaned.split()
        for i in range(len(words) - 1):
            tokens.add(f"{words[i]} {words[i+1]}")
        return tokens

    def _fallback_heuristic_analysis(self, request: RoutingRequest) -> CapabilityAnalysis:
        """Robust fallback heuristic when local qwen3:0.6b is offline or unpulled."""
        text_tokens = self._extract_tokens(request.goal)
        file_extensions = {f.lower().split(".")[-1] for f in request.attached_files if "." in f}

        matched_vision = [k for k in self.VISION_KEYWORDS if k in text_tokens or any(k in f.lower() for f in request.attached_files)]
        matched_coding = [k for k in self.CODING_KEYWORDS if k in text_tokens]
        matched_reasoning = [k for k in self.REASONING_KEYWORDS if k in text_tokens]
        matched_rag = [k for k in self.RAG_KEYWORDS if k in text_tokens]

        has_image_files = any(ext in {"png", "jpg", "jpeg", "tif", "tiff", "bmp", "pdf"} for ext in file_extensions)
        has_code_files = any(ext in {"py", "sh", "sql", "js", "ts"} for ext in file_extensions)

        requires_vision = bool(matched_vision or has_image_files)
        requires_coding = bool(matched_coding or has_code_files)
        requires_reasoning = True
        requires_rag = bool(matched_rag)
        requires_sandbox = requires_coding and any(k in text_tokens for k in {"test", "run", "verify", "execute", "sandbox"})

        target_artifact: Optional[ArtifactType] = None
        if "approval" in request.goal.lower() or "docx" in text_tokens:
            target_artifact = ArtifactType.DOCX
        elif "xlsx" in text_tokens or "excel" in text_tokens:
            target_artifact = ArtifactType.XLSX
        elif requires_coding:
            target_artifact = ArtifactType.PYTHON

        requires_artifact = target_artifact is not None

        if requires_vision and ("p&id" in text_tokens or "drawing" in text_tokens or "diagram" in text_tokens):
            task_type = TaskType.MULTIMODAL_PID
        elif requires_vision and (requires_artifact or "inspection" in text_tokens or "report" in text_tokens):
            task_type = TaskType.DOCUMENT_ANALYSIS
        elif target_artifact == ArtifactType.DOCX and "approval" in text_tokens:
            task_type = TaskType.APPROVAL_NOTE_GENERATION
        elif requires_coding:
            task_type = TaskType.CODING
        elif any(k in text_tokens for k in {"calculate", "calculation", "efficiency", "formula"}):
            task_type = TaskType.ENGINEERING_CALC
        else:
            task_type = TaskType.GENERAL_REASONING

        detected_caps: List[str] = []
        if requires_vision:
            detected_caps.extend(["vision", "multimodal", "ocr"])
        if requires_coding:
            detected_caps.extend(["coding", "python", "code_reasoning"])
        if requires_reasoning:
            detected_caps.extend(["reasoning", "planning"])
        if requires_rag:
            detected_caps.append("rag")
        if requires_sandbox:
            detected_caps.append("sandbox_execution")
        if requires_artifact:
            detected_caps.append("artifact_generation")

        return CapabilityAnalysis(
            task_type=task_type,
            detected_capabilities=list(set(detected_caps)),
            requires_vision=requires_vision,
            requires_coding=requires_coding,
            requires_reasoning=requires_reasoning,
            requires_rag=requires_rag,
            requires_sandbox=requires_sandbox,
            requires_artifact_generation=requires_artifact,
            target_artifact_type=target_artifact,
            matched_keywords={
                "vision": matched_vision,
                "coding": matched_coding,
                "reasoning": matched_reasoning,
                "rag": matched_rag,
            },
        )

    def analyze_capabilities(self, request: RoutingRequest) -> CapabilityAnalysis:
        """Extract required capabilities using qwen3:0.6b classification with fallback."""
        ai_res = self._classify_with_qwen_sync(request)
        file_extensions = {f.lower().split(".")[-1] for f in request.attached_files if "." in f}
        text_tokens = self._extract_tokens(request.goal)

        # Baseline checks
        has_img = any(ext in {"png", "jpg", "jpeg", "tif", "tiff", "bmp", "pdf"} for ext in file_extensions)
        has_sop = any(k in text_tokens for k in self.RAG_KEYWORDS)
        has_code = any(k in text_tokens for k in self.CODING_KEYWORDS) or any(ext in {"py", "sh", "sql", "js", "ts"} for ext in file_extensions)
        has_docx = "approval" in request.goal.lower() or "docx" in text_tokens or "approval note" in request.goal.lower()

        if ai_res:
            # Guardrail overrides
            req_vision = bool(ai_res.get("requires_vision") or has_img or "scan" in text_tokens)
            req_coding = bool(has_code or (ai_res.get("requires_coding") and any(k in text_tokens for k in {"code", "python", "script", "test", "calc", "formula"})))
            req_rag = bool(ai_res.get("requires_rag") or has_sop)
            req_sandbox = bool(ai_res.get("requires_sandbox") or (req_coding and any(k in text_tokens for k in {"test", "run", "sandbox"})))

            target_art: Optional[ArtifactType] = None
            if has_docx:
                target_art = ArtifactType.DOCX
            elif req_coding:
                target_art = ArtifactType.PYTHON
            elif ai_res.get("target_artifact"):
                try:
                    target_art = ArtifactType(ai_res["target_artifact"])
                except Exception:
                    pass

            if req_coding:
                task_type = TaskType.CODING
            elif req_vision and ("p&id" in text_tokens or "drawing" in text_tokens):
                task_type = TaskType.MULTIMODAL_PID
            elif req_vision:
                task_type = TaskType.DOCUMENT_ANALYSIS
            elif "approval" in request.goal.lower():
                task_type = TaskType.APPROVAL_NOTE_GENERATION
            elif any(k in text_tokens for k in {"calculate", "calculation", "efficiency", "formula"}):
                task_type = TaskType.ENGINEERING_CALC
            else:
                task_type = TaskType.GENERAL_REASONING

            caps = []
            if req_vision:
                caps.extend(["vision", "multimodal", "ocr"])
            if req_coding:
                caps.extend(["coding", "python", "code_reasoning"])
            caps.extend(["reasoning", "planning"])
            if req_rag:
                caps.append("rag")
            if req_sandbox:
                caps.append("sandbox_execution")
            if target_art:
                caps.append("artifact_generation")

            return CapabilityAnalysis(
                task_type=task_type,
                detected_capabilities=list(set(caps)),
                requires_vision=req_vision,
                requires_coding=req_coding,
                requires_reasoning=True,
                requires_rag=req_rag,
                requires_sandbox=req_sandbox,
                requires_artifact_generation=target_art is not None,
                target_artifact_type=target_art,
                matched_keywords={"ai_classifier": [self.ROUTER_MODEL]},
            )

        return self._fallback_heuristic_analysis(request)

    def _score_model_for_task(self, model: ModelDefinition, analysis: CapabilityAnalysis) -> ModelScore:
        """Calculate transparent candidate score for UI visualization."""
        matched_caps = []
        for req_cap in analysis.detected_capabilities:
            for mod_cap in model.capabilities:
                if req_cap.lower() in mod_cap.lower() or mod_cap.lower() in req_cap.lower():
                    matched_caps.append(req_cap)
                    break
        matched_caps = list(set(matched_caps))

        cap_score = min(1.0, len(matched_caps) / max(1, len(analysis.detected_capabilities))) if analysis.detected_capabilities else 0.5
        task_fit = 0.4
        if analysis.requires_coding and model.role == ModelRole.CODING:
            task_fit = 1.0
        elif analysis.requires_vision and model.role == ModelRole.VISION:
            task_fit = 1.0
        elif (not analysis.requires_coding and not analysis.requires_vision) and model.role == ModelRole.REASONING:
            task_fit = 1.0
        elif model.role == ModelRole.REASONING:
            task_fit = 0.8

        hw_fit = 1.0 if model.enabled else 0.0
        total = round((0.50 * cap_score) + (0.35 * task_fit) + (0.15 * hw_fit), 2)

        return ModelScore(
            model_name=model.name,
            display_name=model.display_name,
            total_score=total,
            capability_score=round(cap_score, 2),
            task_fit_score=round(task_fit, 2),
            hardware_fit_score=round(hw_fit, 2),
            matched_capabilities=matched_caps,
            is_available=model.enabled,
            explanation=f"Role: {model.role.value.upper()}. Matched: {len(matched_caps)} capabilities.",
        )

    def route_task(self, request: RoutingRequest) -> RoutingDecision:
        """End-to-end routing driven by qwen3:0.6b router with fallback."""
        ai_res = self._classify_with_qwen_sync(request)
        analysis = self.analyze_capabilities(request)

        # Candidate scores for candidate models (excluding router itself)
        candidate_models = [m for m in self.registry.list_models(enabled_only=False) if m.role != ModelRole.ROUTING]
        scores = [self._score_model_for_task(m, analysis) for m in candidate_models]
        scores.sort(key=lambda s: (s.is_available, s.total_score), reverse=True)

        stages: List[StageRouting] = []
        stage_models: Dict[str, str] = {}
        coding_model = self.registry.get_model_for_role(ModelRole.CODING)
        reasoning_model = self.registry.get_model_for_role(ModelRole.REASONING)
        vision_model = self.registry.get_model_for_role(ModelRole.VISION)
        router_model = self.registry.get_model_for_role(ModelRole.ROUTING)

        if analysis.requires_vision:
            stages.append(StageRouting(
                stage_name="vision_ocr_extraction",
                required_capability="multimodal_vision",
                selected_model=vision_model,
                reason="Multimodal vision model selected for visual extraction.",
            ))
            stage_models["vision"] = vision_model

        if analysis.requires_coding:
            stages.append(StageRouting(
                stage_name="code_generation_and_testing",
                required_capability="python_coding",
                selected_model=coding_model,
                reason="Coding specialist selected for syntax correctness.",
            ))
            stage_models["coding"] = coding_model

        if not analysis.requires_coding or analysis.requires_artifact_generation or analysis.requires_rag:
            stages.append(StageRouting(
                stage_name="reasoning_and_synthesis",
                required_capability="reasoning_planning",
                selected_model=reasoning_model,
                reason="Primary reasoning model selected for ReAct orchestration.",
            ))
            stage_models["reasoning"] = reasoning_model

        # Determine Primary Model: Assign specialist models based on classified requirements
        if request.preferred_model:
            primary_model = request.preferred_model
            routing_reason = f"User override: {request.preferred_model}"
        elif analysis.requires_coding or (ai_res and ai_res.get("task_type") == "coding"):
            primary_model = coding_model
            routing_reason = (ai_res and ai_res.get("routing_reason")) or f"Coding capability required: Routed to {coding_model} for verified script execution."
        elif analysis.requires_vision and not analysis.requires_coding:
            primary_model = vision_model
            routing_reason = (ai_res and ai_res.get("routing_reason")) or f"Vision capability required: Routed to {vision_model} for visual document/drawing understanding."
        elif ai_res and ai_res.get("primary_model"):
            cand = ai_res["primary_model"].lower()
            if "coder" in cand or "code" in cand:
                primary_model = coding_model
            elif "vl" in cand or "vision" in cand:
                primary_model = vision_model
            else:
                primary_model = reasoning_model
            routing_reason = ai_res.get("routing_reason") or f"Lightweight AI router ({router_model}) selected {primary_model}."
        else:
            primary_model = reasoning_model
            routing_reason = f"General/Reasoning task: Routed to {reasoning_model} for high-order planning and knowledge synthesis."

        alternatives = [s.model_name for s in scores if s.model_name != primary_model and s.is_available]

        pipeline_str = " -> ".join([f"{st.stage_name} ({st.selected_model})" for st in stages]) if stages else primary_model
        source_classifier = f"Local AI Router ({self.ROUTER_MODEL})" if ai_res else "Local Deterministic Heuristic"
        explanation = (
            f"Decision Engine: {source_classifier}. Task: '{analysis.task_type.value}'. "
            f"Primary Model: {primary_model}. Multi-stage pipeline: {pipeline_str}."
        )

        return RoutingDecision(
            task_type=analysis.task_type,
            primary_model=primary_model,
            stage_models=stage_models,
            stages=stages,
            required_capabilities=analysis.detected_capabilities,
            candidate_scores=scores,
            alternatives=alternatives,
            requires_sandbox=analysis.requires_sandbox,
            requires_rag=analysis.requires_rag,
            target_artifact=analysis.target_artifact_type,
            routing_reason=routing_reason,
            explanation=explanation,
        )
