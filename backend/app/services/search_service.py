import logging
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.schemas.chunk import SearchRequest, SearchResponse, SearchResultItem, SearchMode
from app.services.embeddings import get_embedding_provider
from app.services.search import get_search_index, LocalSearchIndex

logger = logging.getLogger("engineering_copilot.search_service")


class SearchService:
    """Retrieval service orchestrating keyword, vector, and hybrid search across chunks."""

    @staticmethod
    async def ensure_index_hydrated(db: AsyncSession) -> None:
        """
        If using LocalSearchIndex and in-memory store is empty,
        hydrate chunks from PostgreSQL so searches work after application restarts.
        """
        search_index = get_search_index()
        if isinstance(search_index, LocalSearchIndex) and len(search_index._store) == 0:
            query = select(DocumentChunk, Document).join(
                Document, DocumentChunk.document_id == Document.id
            )
            result = await db.execute(query)
            rows = result.all()
            if rows:
                logger.info(f"Hydrating {len(rows)} existing chunks from database into LocalSearchIndex...")
                payload = [
                    {
                        "chunk_id": chunk.id,
                        "document_id": chunk.document_id,
                        "page_id": chunk.page_id,
                        "chunk_index": chunk.chunk_index,
                        "page_number": chunk.page_number,
                        "filename": doc.filename,
                        "document_type": doc.document_type,
                        "part_number": doc.part_number,
                        "revision": doc.revision,
                        "content": chunk.content,
                        "embedding": chunk.embedding,
                        "metadata": chunk.metadata_payload or {},
                    }
                    for chunk, doc in rows
                ]
                await search_index.index_chunks(payload)
                logger.info(f"Hydration complete: {len(payload)} chunks loaded in LocalSearchIndex.")

    @staticmethod
    async def execute_search(
        db: AsyncSession,
        search_req: SearchRequest
    ) -> SearchResponse:
        """Execute hybrid/keyword/vector search with metadata filtering."""
        # Ensure local store is hydrated if starting fresh
        await SearchService.ensure_index_hydrated(db)

        search_index = get_search_index()

        query_vector = None
        mode = search_req.mode
        if mode in (SearchMode.VECTOR, SearchMode.HYBRID):
            emb_provider = get_embedding_provider()
            query_vector = await emb_provider.embed_query(search_req.query)

        filter_dict = None
        if search_req.filters:
            filter_dict = {
                k: v for k, v in search_req.filters.model_dump().items()
                if v is not None
            }

        hits = await search_index.search(
            query=search_req.query,
            query_vector=query_vector,
            top_k=search_req.top_k,
            mode=mode.value,
            filters=filter_dict,
        )

        result_items = [
            SearchResultItem(
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                page_id=hit.page_id,
                page_number=hit.page_number,
                chunk_index=hit.chunk_index,
                filename=hit.filename,
                document_type=hit.document_type,
                part_number=hit.part_number,
                revision=hit.revision,
                content=hit.content,
                score=hit.score,
                retrieval_mode=hit.retrieval_mode,
                metadata=hit.metadata,
            )
            for hit in hits
        ]

        return SearchResponse(
            query=search_req.query,
            mode=mode.value,
            total_results=len(result_items),
            results=result_items,
        )
