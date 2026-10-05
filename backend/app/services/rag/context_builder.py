import logging
from typing import List, Tuple, Dict, Any

from app.schemas.chunk import SearchResultItem
from app.schemas.rag import CitationItem

logger = logging.getLogger("engineering_copilot.rag.context")


class ContextBuilder:
    """
    Constructs structured, provenance-preserving evidence contexts from retrieved search hits.
    Assigns sequential citation identifiers ([C1], [C2], etc.) and packages data inside
    an untrusted data block.
    """

    @staticmethod
    def build_context(
        hits: List[SearchResultItem],
        max_snippet_chars: int = 280,
    ) -> Tuple[str, List[CitationItem], Dict[str, CitationItem]]:
        """
        Assemble retrieved hits into a prompt-ready context string and citation registry.

        Returns:
            context_string: Prompt block wrapped in <engineering_context> tags.
            citations: List of CitationItem objects.
            citation_map: Mapping from citation_id ('C1') to CitationItem.
        """
        if not hits:
            return "", [], {}

        context_blocks: List[str] = []
        citations: List[CitationItem] = []
        citation_map: Dict[str, CitationItem] = {}

        for i, hit in enumerate(hits, start=1):
            citation_id = f"C{i}"

            # Extract section title from metadata if available
            section_title = hit.metadata.get("section") or "General"

            # Clean and truncate snippet for citation card
            content_clean = hit.content.strip()
            snippet = content_clean[:max_snippet_chars]
            if len(content_clean) > max_snippet_chars:
                snippet += "..."

            citation_item = CitationItem(
                citation_id=citation_id,
                document_id=hit.document_id,
                filename=hit.filename,
                page_number=hit.page_number,
                chunk_id=hit.chunk_id,
                chunk_index=hit.chunk_index,
                part_number=hit.part_number,
                revision=hit.revision,
                section=section_title,
                snippet=snippet,
            )
            citations.append(citation_item)
            citation_map[citation_id] = citation_item

            # Format in-context evidence block
            block_lines = [
                f"--- [{citation_id}] ---",
                f"Document: {hit.filename} (ID: {hit.document_id})",
                f"Type: {hit.document_type} | Part: {hit.part_number or 'N/A'} | Rev: {hit.revision or 'N/A'}",
                f"Location: Page {hit.page_number}, Chunk #{hit.chunk_index}",
                f"Section: {section_title}",
                "Content:",
                content_clean,
            ]
            context_blocks.append("\n".join(block_lines))

        raw_context = "\n\n".join(context_blocks)
        full_context_str = (
            "<engineering_context>\n"
            f"{raw_context}\n"
            "</engineering_context>"
        )

        return full_context_str, citations, citation_map
