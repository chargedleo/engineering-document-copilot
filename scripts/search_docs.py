#!/usr/bin/env python3
"""
Engineering Document Search CLI
Query engineering document chunks using keyword, vector, or hybrid retrieval.
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

from app.core.database import AsyncSessionLocal
from app.schemas.chunk import SearchRequest, SearchMode, SearchFilters
from app.services.search_service import SearchService

logging.basicConfig(level=logging.WARNING)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("engineering_copilot").setLevel(logging.WARNING)


async def run_search(
    query: str,
    mode: str = "hybrid",
    top_k: int = 5,
    document_type: str = None,
    part_number: str = None,
):
    search_mode = SearchMode(mode.lower())
    filters = None
    if document_type or part_number:
        filters = SearchFilters(document_type=document_type, part_number=part_number)

    req = SearchRequest(
        query=query,
        mode=search_mode,
        top_k=top_k,
        filters=filters,
    )

    async with AsyncSessionLocal() as session:
        response = await SearchService.execute_search(session, req)

    print("\n" + "=" * 70)
    print(f"  SEARCH QUERY : '{response.query}'")
    print(f"  MODE         : {response.mode.upper()}")
    print(f"  TOTAL HITS   : {response.total_results}")
    print("=" * 70)

    if not response.results:
        print("  No matching chunks found.\n")
        return

    for i, res in enumerate(response.results, start=1):
        print(f"\n  [Hit {i}] Score: {res.score:.4f} | Mode: {res.retrieval_mode}")
        print(f"  Document    : {res.filename} (ID: {res.document_id})")
        print(f"  Location    : Page {res.page_number}, Chunk #{res.chunk_index}")
        if res.part_number:
            print(f"  Part Number : {res.part_number}")
        if res.revision:
            print(f"  Revision    : {res.revision}")
        section = res.metadata.get("section")
        if section:
            print(f"  Section     : {section}")
        print("  Snippet     :")
        for line in res.content.splitlines()[:6]:
            print(f"    {line}")
        if len(res.content.splitlines()) > 6:
            print("    ...")
    print("\n" + "=" * 70 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Search Engineering Document Intelligence Chunks")
    parser.add_argument("query", type=str, help="Search query string (e.g. 'impeller torque 120 Nm')")
    parser.add_argument(
        "--mode",
        type=str,
        default="hybrid",
        choices=["keyword", "vector", "hybrid"],
        help="Retrieval mode: keyword, vector, or hybrid (default: hybrid)",
    )
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return (default: 5)")
    parser.add_argument("--document-type", type=str, default=None, help="Filter by document type")
    parser.add_argument("--part-number", type=str, default=None, help="Filter by part number")

    args = parser.parse_args()
    asyncio.run(
        run_search(
            query=args.query,
            mode=args.mode,
            top_k=args.top_k,
            document_type=args.document_type,
            part_number=args.part_number,
        )
    )


if __name__ == "__main__":
    main()
