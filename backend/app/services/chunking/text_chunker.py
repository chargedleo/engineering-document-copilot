import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from app.core.config import settings

logger = logging.getLogger("engineering_copilot.chunker")


@dataclass
class PageInput:
    page_id: Optional[str]
    page_number: int
    text: str


@dataclass
class ChunkOutput:
    chunk_index: int  # 0-indexed across the document
    page_id: Optional[str]
    page_number: int
    content: str
    character_count: int
    word_count: int
    metadata_payload: Dict[str, Any] = field(default_factory=dict)


# Regex patterns identifying engineering section headers and list items
SECTION_HEADER_PATTERN = re.compile(
    r"^(?:(?:\d+\.|\d+\.\d+|\d+\.\d+\.\d+)\s+[A-Z0-9\s\-_/&]+|[A-Z0-9\s\-_/&]{4,}:?)$",
    re.MULTILINE
)


def extract_section_title(text_block: str) -> Optional[str]:
    """Extract first heading or title line from a text block if present."""
    lines = [line.strip() for line in text_block.splitlines() if line.strip()]
    if not lines:
        return None
    first_line = lines[0]
    # Check if first line matches numbered section or all-caps header
    if re.match(r"^\d+\.?\s+[A-Z]", first_line) or (first_line.isupper() and len(first_line) > 3):
        return first_line[:120]
    return None


class EngineeringDocumentChunker:
    """
    Structural chunker optimized for technical engineering specifications,
    operating manuals, datasheets, and standards.

    Preserves:
    - Units (e.g. bar, psi, mm, m3/h, RPM, Nm, C, Hz)
    - Tolerances (e.g. +/- 0.5 bar, +0.030 / -0.000 mm, ISO h6/H7)
    - Part numbers (e.g. CFP-402-316L, TC-500-ENG)
    - Revisions (e.g. Rev D, Revision: A)
    - Technical bullet lists and numbered paragraphs
    - Page boundaries and document provenance
    """

    def __init__(
        self,
        chunk_size_chars: Optional[int] = None,
        chunk_overlap_chars: Optional[int] = None,
    ):
        self.chunk_size_chars = chunk_size_chars or settings.CHUNK_SIZE_CHARS
        self.chunk_overlap_chars = chunk_overlap_chars or settings.CHUNK_OVERLAP_CHARS

    def chunk_document_pages(
        self,
        pages: List[PageInput],
        document_metadata: Dict[str, Any]
    ) -> List[ChunkOutput]:
        """
        Produce sequential, deterministic chunks from a document's extracted pages.
        """
        chunks: List[ChunkOutput] = []
        global_chunk_idx = 0
        current_section = "General"

        doc_id = document_metadata.get("document_id", "")
        filename = document_metadata.get("filename", "")
        doc_type = document_metadata.get("document_type", "SPECIFICATION")
        part_number = document_metadata.get("part_number")
        revision = document_metadata.get("revision", "A")

        for page in pages:
            raw_text = (page.text or "").strip()
            if not raw_text:
                continue

            # Check if this page introduces a new major section
            heading = extract_section_title(raw_text)
            if heading:
                current_section = heading

            # Split page into logical paragraphs / subsections
            paragraphs = self._split_into_logical_blocks(raw_text)

            accumulated_blocks: List[str] = []
            accumulated_len = 0

            for para in paragraphs:
                para_len = len(para)

                # If paragraph itself is larger than chunk_size, split by lines or sentences
                if para_len > self.chunk_size_chars:
                    # Flush any accumulated blocks first
                    if accumulated_blocks:
                        chunk_text = "\n\n".join(accumulated_blocks).strip()
                        if chunk_text:
                            chunks.append(
                                self._create_chunk(
                                    chunk_index=global_chunk_idx,
                                    page=page,
                                    content=chunk_text,
                                    section=current_section,
                                    doc_meta=document_metadata
                                )
                            )
                            global_chunk_idx += 1
                        accumulated_blocks = []
                        accumulated_len = 0

                    sub_chunks = self._split_large_block(para)
                    for sc in sub_chunks:
                        chunks.append(
                            self._create_chunk(
                                chunk_index=global_chunk_idx,
                                page=page,
                                content=sc,
                                section=current_section,
                                doc_meta=document_metadata
                            )
                        )
                        global_chunk_idx += 1
                    continue

                # Check if adding this paragraph exceeds target chunk size
                if accumulated_len + para_len + 2 > self.chunk_size_chars and accumulated_blocks:
                    # Flush current chunk
                    chunk_text = "\n\n".join(accumulated_blocks).strip()
                    chunks.append(
                        self._create_chunk(
                            chunk_index=global_chunk_idx,
                            page=page,
                            content=chunk_text,
                            section=current_section,
                            doc_meta=document_metadata
                        )
                    )
                    global_chunk_idx += 1

                    # Apply overlap: carry over trailing text if overlap is configured
                    overlap_block = self._get_overlap_text(chunk_text)
                    if overlap_block:
                        accumulated_blocks = [overlap_block, para]
                        accumulated_len = len(overlap_block) + len(para) + 2
                    else:
                        accumulated_blocks = [para]
                        accumulated_len = para_len
                else:
                    accumulated_blocks.append(para)
                    accumulated_len += para_len + 2

            # Flush remaining accumulated text for this page
            if accumulated_blocks:
                chunk_text = "\n\n".join(accumulated_blocks).strip()
                if chunk_text:
                    chunks.append(
                        self._create_chunk(
                            chunk_index=global_chunk_idx,
                            page=page,
                            content=chunk_text,
                            section=current_section,
                            doc_meta=document_metadata
                        )
                    )
                    global_chunk_idx += 1

        logger.info(
            f"Chunked document {filename} ({len(pages)} pages) -> {len(chunks)} structural chunks."
        )
        return chunks

    def _split_into_logical_blocks(self, text: str) -> List[str]:
        """Split text on double newlines (paragraphs/subsections)."""
        raw_blocks = re.split(r"\n\s*\n", text)
        clean_blocks = [b.strip() for b in raw_blocks if b.strip()]
        return clean_blocks

    def _split_large_block(self, large_text: str) -> List[str]:
        """
        Split an oversized block first by lines, and if any line exceeds chunk_size_chars,
        by sentences or words to protect units, tolerances, and equations.
        """
        lines = large_text.splitlines()
        chunks: List[str] = []
        current_lines: List[str] = []
        current_len = 0

        # Break lines down further if any individual line exceeds chunk_size_chars
        sub_elements: List[str] = []
        for line in lines:
            if len(line) > self.chunk_size_chars:
                # Split by sentence or punctuation boundaries
                sentences = re.split(r"(?<=[.!?])\s+", line)
                curr_sent: List[str] = []
                curr_sent_len = 0
                for s in sentences:
                    if curr_sent_len + len(s) + 1 > self.chunk_size_chars and curr_sent:
                        sub_elements.append(" ".join(curr_sent))
                        curr_sent = [s]
                        curr_sent_len = len(s)
                    else:
                        curr_sent.append(s)
                        curr_sent_len += len(s) + 1
                if curr_sent:
                    for sent_item in curr_sent:
                        if len(sent_item) > self.chunk_size_chars:
                            words = sent_item.split()
                            w_accum: List[str] = []
                            w_len = 0
                            for w in words:
                                if w_len + len(w) + 1 > self.chunk_size_chars and w_accum:
                                    sub_elements.append(" ".join(w_accum))
                                    w_accum = [w]
                                    w_len = len(w)
                                else:
                                    w_accum.append(w)
                                    w_len += len(w) + 1
                            if w_accum:
                                sub_elements.append(" ".join(w_accum))
                        else:
                            sub_elements.append(sent_item)
            else:
                sub_elements.append(line)

        for el in sub_elements:
            el_len = len(el)
            if current_len + el_len + 1 > self.chunk_size_chars and current_lines:
                chunks.append("\n".join(current_lines).strip())
                current_lines = [el]
                current_len = el_len
            else:
                current_lines.append(el)
                current_len += el_len + 1

        if current_lines:
            chunks.append("\n".join(current_lines).strip())

        return [c for c in chunks if c.strip()]

    def _get_overlap_text(self, chunk_text: str) -> Optional[str]:
        """Extract a meaningful trailing overlap segment from a flushed chunk."""
        if self.chunk_overlap_chars <= 0:
            return None
        lines = chunk_text.splitlines()
        overlap_lines: List[str] = []
        accum = 0
        for line in reversed(lines):
            line_len = len(line)
            if accum + line_len <= self.chunk_overlap_chars:
                overlap_lines.insert(0, line)
                accum += line_len + 1
            else:
                break
        if overlap_lines:
            return "\n".join(overlap_lines)
        return None

    def _create_chunk(
        self,
        chunk_index: int,
        page: PageInput,
        content: str,
        section: str,
        doc_meta: Dict[str, Any]
    ) -> ChunkOutput:
        metadata = {
            "document_id": doc_meta.get("document_id"),
            "filename": doc_meta.get("filename"),
            "document_type": doc_meta.get("document_type"),
            "part_number": doc_meta.get("part_number"),
            "revision": doc_meta.get("revision"),
            "page_number": page.page_number,
            "chunk_index": chunk_index,
            "section": section,
        }
        return ChunkOutput(
            chunk_index=chunk_index,
            page_id=page.page_id,
            page_number=page.page_number,
            content=content,
            character_count=len(content),
            word_count=len(content.split()),
            metadata_payload=metadata
        )
