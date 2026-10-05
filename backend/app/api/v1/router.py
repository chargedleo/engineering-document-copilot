from fastapi import APIRouter
from app.api.v1.endpoints import health, documents, cad, chat, search

api_router = APIRouter()

api_router.include_router(health.router, prefix="/health", tags=["Health & Status"])
api_router.include_router(documents.router, prefix="/documents", tags=["Engineering Documents"])
api_router.include_router(search.router, prefix="/search", tags=["Hybrid Search"])
api_router.include_router(cad.router, prefix="/cad", tags=["CAD Knowledge"])
api_router.include_router(chat.router, prefix="/chat", tags=["Copilot Chat"])

