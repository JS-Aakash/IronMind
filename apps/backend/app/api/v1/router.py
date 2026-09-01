from fastapi import APIRouter

from apps.backend.app.api.v1.endpoints import (
    artifacts,
    audit,
    documents,
    health,
    knowledge,
    models,
    router as model_router,
    sandbox,
    sovereignty,
    tasks,
    tools,
)

api_router = APIRouter()

# Register core health check under /api/v1 and root
api_router.include_router(health.router)
api_router.include_router(tasks.router)
api_router.include_router(models.router)
api_router.include_router(model_router.router)
api_router.include_router(tools.router, prefix="/tools", tags=["tools"])
api_router.include_router(sandbox.router, prefix="/sandbox", tags=["sandbox"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(knowledge.router)
api_router.include_router(artifacts.router)
api_router.include_router(sovereignty.router)
api_router.include_router(audit.router)
