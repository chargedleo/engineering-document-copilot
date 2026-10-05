from fastapi import APIRouter
from app.api.v1.endpoints import health, documents, cad, chat, search, rag, agent

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health & Status"])
api_router.include_router(documents.router, prefix="/documents", tags=["Engineering Documents"])
api_router.include_router(search.router, prefix="/search", tags=["Hybrid Search"])
api_router.include_router(rag.router, prefix="/rag", tags=["RAG & Copilot"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agentic Copilot"])
api_router.include_router(cad.router, prefix="/cad", tags=["CAD Knowledge"])
api_router.include_router(chat.router, prefix="/chat", tags=["Copilot Chat"])

