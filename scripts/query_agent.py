#!/usr/bin/env python3
"""
LangGraph Engineering Copilot Agent CLI Demonstration
Execute autonomous question-answering with tool selection, execution traces,
and grounded engineering citations.
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.database import AsyncSessionLocal, engine
from app.schemas.chunk import SearchFilters
from app.schemas.agent import AgentQueryRequest
from app.services.agent_service import AgentService

# Suppress engine query echoing in CLI output
engine.echo = False
logging.basicConfig(level=logging.ERROR)
for log_name in ("sqlalchemy.engine", "sqlalchemy.pool", "sqlalchemy.dialects", "engineering_copilot"):
    l = logging.getLogger(log_name)
    l.setLevel(logging.ERROR)
    l.propagate = False


async def run_agent_query(
    query: str,
    top_k: int = 5,
    part_number: str = None,
    revision: str = None,
):
    filters = None
    if part_number or revision:
        filters = SearchFilters(
            part_number=part_number,
            revision=revision,
        )

    req = AgentQueryRequest(
        query=query,
        top_k=top_k,
        filters=filters,
    )

    async with AsyncSessionLocal() as session:
        response = await AgentService.run_agent(session, req)

    print("\n" + "=" * 80)
    print("  ATLAS COPCO GECIA - ENGINEERING COPILOT (LANGGRAPH AGENT)")
    print("=" * 80)
    print(f"  QUESTION    : {response.query}")
    print(f"  PROVIDER    : {response.metadata.get('provider')} ({response.metadata.get('model')})")
    print(f"  STATUS      : {'Abstained / Insufficient Evidence' if response.should_abstain else 'Grounded Synthesis Complete'}")
    print(f"  LATENCY     : {response.metadata.get('latency_ms', 0):.1f} ms")
    print(f"  TOOLS USED  : {', '.join(response.tools_used) if response.tools_used else 'None (Direct Response)'}")
    print("-" * 80)

    # Tool Execution Trace Summary
    if response.tool_traces:
        print("  TOOL EXECUTION TRACE:")
        for i, trace in enumerate(response.tool_traces, start=1):
            status_indicator = "[OK]" if trace.status == "success" else "[ERROR]"
            print(f"    [{i}] {status_indicator} {trace.tool_name}")
            if trace.input_summary:
                clean_inputs = {k: v for k, v in trace.input_summary.items() if v is not None}
                print(f"        Input  : {clean_inputs}")
            if trace.output_summary:
                print(f"        Output : {trace.output_summary}")
            if trace.error:
                print(f"        Error  : {trace.error}")
        print("-" * 80)

    print("\n  ANSWER:\n")
    for line in response.answer.splitlines():
        print(f"    {line}")
    print()

    # Citations
    if response.citations:
        print("-" * 80)
        print(f"  GROUNDED CITATIONS ({len(response.citations)} verified):")
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
            print("      Excerpt:")
            for s_line in cit.snippet.splitlines()[:3]:
                print(f"        {s_line}")
            if len(cit.snippet.splitlines()) > 3:
                print("        ...")
    else:
        print("-" * 80)
        print("  GROUNDED CITATIONS: None (Abstained or pure mathematical calculation)")

    print("\n" + "=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Query the LangGraph Engineering Copilot Agent with tool selection and citations."
    )
    parser.add_argument(
        "query",
        type=str,
        help="Technical question or calculation (e.g. 'What is the working pressure in psi?')",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum candidate chunks for document search (default: 5)",
    )
    parser.add_argument(
        "--part-number",
        type=str,
        default=None,
        help="Filter by engineering part number (e.g. CFP-402-316L)",
    )
    parser.add_argument(
        "--revision",
        type=str,
        default=None,
        help="Filter by revision identifier (e.g. D)",
    )

    args = parser.parse_args()
    asyncio.run(
        run_agent_query(
            query=args.query,
            top_k=args.top_k,
            part_number=args.part_number,
            revision=args.revision,
        )
    )


if __name__ == "__main__":
    main()
