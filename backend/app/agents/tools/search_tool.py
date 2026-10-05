import logging
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chunk import SearchRequest, SearchMode, SearchFilters
from app.services.search_service import SearchService

logger = logging.getLogger("engineering_copilot.agents.tools.search")


class SearchEngineeringDocumentsTool:
    """
    Tool wrapping the M4 hybrid search service.
    Retrieves engineering document chunks via keyword + vector hybrid search (RRF).
    Preserves document ID, filename, page number, revision, chunk ID, section, and score.
    """
    name: str = "search_engineering_documents"
    description: str = (
        "Search indexed engineering documents (manuals, specs, datasheets) "
        "using hybrid keyword + dense vector retrieval. Use this tool when technical "
        "evidence, running clearances, operating limits, pressures, or assembly procedures are required."
    )

    @classmethod
    async def run(
        cls,
        db: AsyncSession,
        query: str,
        top_k: int = 5,
        document_id: Optional[str] = None,
        part_number: Optional[str] = None,
        revision: Optional[str] = None,
        document_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute hybrid search against existing search service."""
        try:
            filters = None
            if document_id or part_number or revision or document_type:
                filters = SearchFilters(
                    document_id=document_id,
                    part_number=part_number,
                    revision=revision,
                    document_type=document_type,
                )

            req = SearchRequest(
                query=query.strip(),
                top_k=top_k,
                mode=SearchMode.HYBRID,
                filters=filters,
            )

            response = await SearchService.execute_search(db, req)

            hits_data: List[Dict[str, Any]] = []
            for hit in response.results:
                hits_data.append({
                    "chunk_id": hit.chunk_id,
                    "document_id": hit.document_id,
                    "chunk_index": hit.chunk_index,
                    "page_number": hit.page_number,
                    "filename": hit.filename,
                    "document_type": hit.document_type,
                    "part_number": hit.part_number,
                    "revision": hit.revision,
                    "score": round(hit.score, 4),
                    "section": hit.metadata.get("section") or "General",
                    "content": hit.content,
                })

            return {
                "success": True,
                "query": query,
                "total_results": response.total_results,
                "retrieval_mode": response.mode,
                "hits": hits_data,
            }
        except Exception as e:
            logger.error(f"Error in search_engineering_documents tool: {e}", exc_info=True)
            return {
                "success": False,
                "query": query,
                "total_results": 0,
                "hits": [],
                "error": str(e),
            }
