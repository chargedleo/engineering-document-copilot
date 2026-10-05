import logging
import re
import time
from typing import List, Set, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.chunk import SearchRequest
from app.schemas.rag import RAGQueryRequest, RAGResponse, CitationItem
from app.services.search_service import SearchService
from app.services.rag.context_builder import ContextBuilder
from app.services.rag.prompt import build_rag_messages
from app.services.llm import get_llm_provider, INSUFFICIENT_INFORMATION_MSG

logger = logging.getLogger("engineering_copilot.rag_service")


class RAGService:
    """
    Retrieval-Augmented Generation service orchestrating query validation,
    hybrid retrieval, context assembly, LLM synthesis, citation extraction,
    and evidence sufficiency checks.
    """

    @staticmethod
    async def answer_question(
        db: AsyncSession,
        request: RAGQueryRequest,
    ) -> RAGResponse:
        start_time = time.perf_counter()

        query_cleaned = request.query.strip()
        if not query_cleaned:
            raise ValueError("Query cannot be empty or contain only whitespace.")

        # 1. Execute hybrid retrieval via existing SearchService
        top_k = request.top_k or settings.RAG_DEFAULT_TOP_K
        search_req = SearchRequest(
            query=query_cleaned,
            top_k=top_k,
            mode=request.retrieval_mode,
            filters=request.filters,
        )

        search_response = await SearchService.execute_search(db, search_req)
        raw_hits = search_response.results

        # 2. Filter hits by relevance threshold
        threshold = settings.RAG_RELEVANCE_THRESHOLD
        candidate_hits = [h for h in raw_hits if h.score >= threshold]

        llm_provider = get_llm_provider()

        # 3. Check for zero evidence or empty retrieval
        if not candidate_hits:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                f"RAG query '{query_cleaned[:40]}...' yielded 0 hits above threshold {threshold} "
                f"({len(raw_hits)} total hits retrieved)."
            )
            return RAGResponse(
                query=query_cleaned,
                answer=INSUFFICIENT_INFORMATION_MSG,
                citations=[],
                retrieved_chunks_count=len(raw_hits),
                retrieval_mode=request.retrieval_mode.value,
                sufficient_evidence=False,
                provider=llm_provider.name,
                model=llm_provider.model_name,
                timing_ms=round(elapsed_ms, 2),
            )

        # 4. Assemble structured evidence context
        context_str, candidate_citations, citation_map = ContextBuilder.build_context(candidate_hits)

        # 5. Build system and user messages
        messages = build_rag_messages(context_str, query_cleaned)

        # 6. Generate answer using configured LLM provider
        llm_response = await llm_provider.generate(messages, temperature=0.0)
        answer_text = llm_response.content.strip()

        # 7. Evaluate sufficiency and extract citations
        is_insufficient = (
            INSUFFICIENT_INFORMATION_MSG.lower() in answer_text.lower()
            or "not contain enough information" in answer_text.lower()
            or "insufficient information" in answer_text.lower()
        )

        if is_insufficient:
            sufficient_evidence = False
            # When abstaining, no factual claims are made, so no supporting citations apply
            active_citations = []
        else:
            sufficient_evidence = True
            # Find all citation identifiers in the answer e.g. [C1], [C2]
            cited_ids: Set[str] = set(re.findall(r"\[(C\d+)\]", answer_text))
            active_citations = [
                citation_map[cid] for cid in sorted(cited_ids) if cid in citation_map
            ]
            # Fallback: if LLM synthesized facts but omitted citation tags, attach top candidate
            if not active_citations and candidate_citations:
                active_citations = [candidate_citations[0]]

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            f"RAG query finished in {elapsed_ms:.1f}ms | Hits: {len(candidate_hits)}/{len(raw_hits)} "
            f"| Citations: {len(active_citations)} | Sufficient: {sufficient_evidence} | Provider: {llm_provider.name}"
        )

        return RAGResponse(
            query=query_cleaned,
            answer=answer_text,
            citations=active_citations,
            retrieved_chunks_count=len(raw_hits),
            retrieval_mode=request.retrieval_mode.value,
            sufficient_evidence=sufficient_evidence,
            provider=llm_provider.name,
            model=llm_provider.model_name,
            timing_ms=round(elapsed_ms, 2),
        )
