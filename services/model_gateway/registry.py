import logging
from typing import Dict, List, Optional
from packages.shared.models.enums import ModelRole
from services.model_gateway.models import ModelDefinition

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Registry maintaining definitions, capabilities, and availability configuration for local models."""

    def __init__(self):
        self._models: Dict[str, ModelDefinition] = {}
        self._initialize_default_models()

    def _initialize_default_models(self) -> None:
        """Register the default open-weight models specified for IronMind."""
        defaults = [
            ModelDefinition(
                name="qwen3:8b",
                display_name="Qwen 3 (8B Instruct)",
                provider="ollama",
                role=ModelRole.REASONING,
                capabilities=[
                    "reasoning",
                    "multi_step_planning",
                    "tool_calling",
                    "document_summarization",
                    "approval_note_drafting",
                ],
                context_length=32768,
                vram_estimate_mb=5000,
                enabled=True,
                description="Primary local reasoning and orchestration model for multi-step agent planning.",
            ),
            ModelDefinition(
                name="qwen2.5-coder:7b",
                display_name="Qwen 2.5 Coder (7B Instruct)",
                provider="ollama",
                role=ModelRole.CODING,
                capabilities=[
                    "python",
                    "code_generation",
                    "unit_testing",
                    "debugging",
                    "data_processing_scripts",
                    "engineering_formulas",
                ],
                context_length=32768,
                vram_estimate_mb=4500,
                enabled=True,
                description="Specialized programming and script verification model for isolated sandbox execution.",
            ),
            ModelDefinition(
                name="qwen2.5vl:7b",
                display_name="Qwen 2.5-VL (7B Multimodal)",
                provider="ollama",
                role=ModelRole.VISION,
                capabilities=[
                    "vision",
                    "multimodal_understanding",
                    "pid_diagram_parsing",
                    "scanned_pdf_ocr",
                    "handwriting_recognition",
                    "table_extraction",
                ],
                context_length=16384,
                vram_estimate_mb=5500,
                enabled=True,
                description="On-premise multimodal vision model for inspecting P&ID drawings, charts, and scanned inspection logs.",
            ),
            ModelDefinition(
                name="qwen3:0.6b",
                display_name="Qwen 3 (0.6B Fast Router)",
                provider="ollama",
                role=ModelRole.ROUTING,
                capabilities=[
                    "routing",
                    "task_classification",
                    "intent_detection",
                    "fast_triage",
                ],
                context_length=8192,
                vram_estimate_mb=450,
                enabled=True,
                description="Ultra-lightweight 0.6B local model dedicated to low-latency capability routing and request triage.",
            ),
        ]
        for m in defaults:
            self._models[m.name] = m

    def register_model(self, model_def: ModelDefinition) -> None:
        """Register a new open-weight model definition."""
        self._models[model_def.name] = model_def
        logger.info("Registered model definition: %s (Provider: %s)", model_def.name, model_def.provider)

    def get_model(self, name: str) -> Optional[ModelDefinition]:
        """Retrieve model definition by identifier or alias."""
        if name in self._models:
            return self._models[name]
        clean_name = name.lower().strip()
        # 1. Exact match (case-insensitive)
        for key, val in self._models.items():
            if key.lower() == clean_name:
                return val
        # 2. Normalized match without hyphens (e.g. qwen2.5-vl:7b vs qwen2.5vl:7b)
        clean_no_hyphen = clean_name.replace("-", "")
        for key, val in self._models.items():
            if key.lower().replace("-", "") == clean_no_hyphen:
                return val
        # 3. Base name match only if no tag was supplied in the request
        if ":" not in clean_name:
            for key, val in self._models.items():
                if key.lower().split(":")[0] == clean_name:
                    return val
        return None

    def list_models(self, enabled_only: bool = True) -> List[ModelDefinition]:
        """List registered models."""
        models = list(self._models.values())
        if enabled_only:
            return [m for m in models if m.enabled]
        return models

    def find_by_role(self, role: ModelRole) -> List[ModelDefinition]:
        """Find models matching a specific role."""
        return [m for m in self._models.values() if m.role == role and m.enabled]

    def find_by_capability(self, capability: str) -> List[ModelDefinition]:
        """Find models supporting a specific capability."""
        return [
            m for m in self._models.values()
            if m.enabled and capability.lower() in [c.lower() for c in m.capabilities]
        ]

    def set_model_enabled(self, name: str, enabled: bool) -> Optional[ModelDefinition]:
        """Enable or disable a model in the registry."""
        model = self.get_model(name)
        if model:
            model.enabled = enabled
            return model
        return None
