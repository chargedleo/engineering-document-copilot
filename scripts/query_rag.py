#!/usr/bin/env python3
"""
Engineering Document Intelligence RAG CLI
Execute grounded question-answering over engineering documents with citations.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to path to allow importing app modules
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.database import AsyncSessionLocal, engine
from app.schemas.chunk import SearchMode, SearchFilters
from app.schemas.rag import RAGQueryRequest
from app.services.rag_service import RAGService

# Suppress engine query echoing in CLI output
engine.echo = False
logging.basicConfig(level=logging.ERROR)
for log_name in ("sqlalchemy.engine", "sqlalchemy.pool", "sqlalchemy.dialects", "engineering_copilot"):
    l = logging.getLogger(log_name)
    l.setLevel(logging.ERROR)
    l.propagate = False


async def run_rag_query(
    query: str,
    mode: str = "hybrid",
    top_k: int = 5,
    part_number: str = None,
    revision: str = None,
    document_type: str = None,
):
    search_mode = SearchMode(mode.lower())
    filters = None
    if part_number or revision or document_type:
        filters = SearchFilters(
            part_number=part_number,
            revision=revision,
            document_type=document_type,
        )

    req = RAGQueryRequest(
        query=query,
        top_k=top_k,
        retrieval_mode=search_mode,
        filters=filters,
    )

    async with AsyncSessionLocal() as session:
        response = await RAGService.answer_question(session, req)

    print("\n" + "=" * 75)
    print("  ENGINEERING COPILOT - GROUNDED RAG RESPONSE")
    print("=" * 75)
    print(f"  QUESTION : {response.query}")
    print(f"  PROVIDER : {response.provider} ({response.model})")
    print(f"  MODE     : {response.retrieval_mode.upper()} (Top-K: {top_k})")
    print(f"  EVIDENCE : {'Sufficient' if response.sufficient_evidence else 'Insufficient / Abstention'}")
    if response.timing_ms:
        print(f"  LATENCY  : {response.timing_ms:.1f} ms")
    print("-" * 75)
    print("\n  ANSWER:\n")
    for line in response.answer.splitlines():
        print(f"    {line}")
    print()

    if response.citations:
        print("-" * 75)
        print(f"  CITATIONS ({len(response.citations)} referenced):")
        for cit in response.citations:
            meta_parts = []
            if cit.part_number:
                meta_parts.append(f"Part: {cit.part_number}")
            if cit.revision:
                meta_parts.append(f"Rev: {cit.revision}")
            if cit.section:
                meta_parts.append(f"Section: {cit.section}")
            meta_str = f" | {', '.join(meta_parts)}" if meta_parts else ""

            print(f"\n  [{cit.citation_id}] {cit.filename} (Page {cit.page_number}, Chunk #{cit.chunk_index}{meta_str})")
            print("      Snippet:")
            for s_line in cit.snippet.splitlines()[:3]:
                print(f"        {s_line}")
            if len(cit.snippet.splitlines()) > 3:
                print("        ...")
    else:
        print("-" * 75)
        print("  CITATIONS: None (Abstained or no relevant evidence matched)")

    print("\n" + "=" * 75 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Ask grounded engineering questions with document citations."
    )
    parser.add_argument(
        "query",
        type=str,
        help="Technical question to ask (e.g. 'What is the radial bearing journal tolerance?')",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="hybrid",
        choices=["keyword", "vector", "hybrid"],
        help="Retrieval mode: keyword, vector, or hybrid (default: hybrid)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Number of candidate chunks to retrieve (default: 5)",
    )
    parser.add_argument(
        "--part-number",
        type=str,
        default=None,
        help="Filter by part number (e.g. CFP-402-316L)",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default=None,
        help="Filter by revision (e.g. D)",
    )
    parser.add_argument(
        "--document-type",
        type=str,
        default=None,
        help="Filter by document type (e.g. specification)",
    )

    args = parser.parse_args()
    asyncio.run(
        run_rag_query(
            query=args.query,
            mode=args.mode,
            top_k=args.top_k,
            part_number=args.part_number,
            revision=args.revision,
            document_type=args.document_type,
        )
    )


if __name__ == "__main__":
    main()
