from functools import lru_cache
from services.agent import AgentService
from services.artifacts import ArtifactsService
from services.audit import AuditService
from services.document_intelligence import DocumentIntelligenceService
from services.model_gateway import ModelGatewayService, ModelRouter, ModelService
from services.rag import RagService
from services.sandbox import SandboxService
from services.sovereignty import SovereigntyService


@lru_cache()
def get_model_gateway_service() -> ModelService:
    return ModelService()


@lru_cache()
def get_model_router() -> ModelRouter:
    return ModelRouter()


@lru_cache()
def get_agent_service() -> AgentService:
    return AgentService()


@lru_cache()
def get_rag_service() -> RagService:
    return RagService()


@lru_cache()
def get_document_intelligence_service() -> DocumentIntelligenceService:
    return DocumentIntelligenceService()


@lru_cache()
def get_sandbox_service() -> SandboxService:
    return SandboxService()


@lru_cache()
def get_artifacts_service() -> ArtifactsService:
    return ArtifactsService()


@lru_cache()
def get_sovereignty_service() -> SovereigntyService:
    return SovereigntyService()


@lru_cache()
def get_audit_service() -> AuditService:
    return AuditService()
