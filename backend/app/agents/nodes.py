import logging
import re
from typing import Dict, Any, List
from langchain_core.runnables import RunnableConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.chunk import SearchResultItem
from app.schemas.rag import CitationItem
from app.services.llm import get_llm_provider, INSUFFICIENT_INFORMATION_MSG
from app.services.rag.context_builder import ContextBuilder
from app.services.rag.prompt import build_rag_messages
from app.agents.state import CopilotAgentState
from app.agents.planner import AgentPlanner
from app.agents.tools import (
    SearchEngineeringDocumentsTool,
    GetDocumentMetadataTool,
    EngineeringCalculatorTool,
)

logger = logging.getLogger("engineering_copilot.agents.nodes")


async def classify_and_plan_node(
    state: CopilotAgentState,
    config: RunnableConfig
) -> Dict[str, Any]:
    """Analyze query and determine required tool calls."""
    query = state.get("user_query", "")
    filters = state.get("filters")
    tool_calls = AgentPlanner.plan(query, filters)
    logger.info(f"Agent planner selected {len(tool_calls)} tool calls for query: '{query[:50]}'")
    return {
        "tool_calls": tool_calls,
        "tools_used": [],
        "tool_results": [],
    }


async def execute_tools_node(
    state: CopilotAgentState,
    config: RunnableConfig
) -> Dict[str, Any]:
    """Execute decided tool calls with database session and collect structured results."""
    db: AsyncSession = config.get("configurable", {}).get("db")
    tool_calls = state.get("tool_calls", [])
    tools_used: List[str] = list(state.get("tools_used", []))
    tool_results: List[Dict[str, Any]] = list(state.get("tool_results", []))

    retrieved_chunks: List[Dict[str, Any]] = []
    metadata_results: Dict[str, Any] = {}
    calculation_results: List[Dict[str, Any]] = []

    for call in tool_calls:
        tool_name = call.get("tool")
        args = call.get("args", {})

        if tool_name == "search_engineering_documents":
            if tool_name not in tools_used:
                tools_used.append(tool_name)
            top_k = args.get("top_k", state.get("top_k", 5))
            res = await SearchEngineeringDocumentsTool.run(
                db=db,
                query=args.get("query", state.get("user_query", "")),
                top_k=top_k,
                part_number=args.get("part_number"),
                revision=args.get("revision"),
                document_id=args.get("document_id"),
            )
            tool_results.append({"tool": tool_name, "status": "success" if res.get("success") else "error", "output": res})
            if res.get("success"):
                retrieved_chunks.extend(res.get("hits", []))

        elif tool_name == "get_document_metadata":
            if tool_name not in tools_used:
                tools_used.append(tool_name)

            part_num = args.get("part_number")
            doc_id = args.get("document_id")
            filename = args.get("filename")

            # Dynamic resolution: If identifiers are missing but search found chunks, infer from top hit
            if not part_num and not doc_id and not filename and retrieved_chunks:
                top_hit = retrieved_chunks[0]
                part_num = top_hit.get("part_number")
                doc_id = top_hit.get("document_id")
                filename = top_hit.get("filename")

            res = await GetDocumentMetadataTool.run(
                db=db,
                document_id=doc_id,
                part_number=part_num,
                filename=filename,
            )
            tool_results.append({"tool": tool_name, "status": "success" if res.get("success") else "error", "output": res})
            if res.get("success") and res.get("found"):
                metadata_results = res

        elif tool_name == "calculate_engineering":
            if tool_name not in tools_used:
                tools_used.append(tool_name)

            op = args.get("operation", "")
            val = args.get("value")
            val2 = args.get("value2")

            # Dynamic extraction: if numerical value was not given directly in query, extract from retrieved chunks
            if val is None and retrieved_chunks:
                for chunk in retrieved_chunks:
                    text = chunk.get("content", "")
                    if op in ("bar_to_psi", "psi_to_bar"):
                        match = re.search(r"(\d+(?:\.\d+)?)\s*bar\b", text, re.IGNORECASE)
                        if match:
                            val = float(match.group(1))
                            break
                    elif op in ("celsius_to_fahrenheit", "fahrenheit_to_celsius"):
                        match = re.search(r"(\d+(?:\.\d+)?)\s*°?C\b", text)
                        if match:
                            val = float(match.group(1))
                            break
                    elif op in ("flow_m3h_to_lpm", "flow_lpm_to_m3h"):
                        match = re.search(r"(\d+(?:\.\d+)?)\s*m[3³]/h\b", text, re.IGNORECASE)
                        if match:
                            val = float(match.group(1))
                            break

            if val is not None:
                res = EngineeringCalculatorTool.run(operation=op, value=val, value2=val2)
                tool_results.append({"tool": tool_name, "status": "success" if res.get("success") else "error", "output": res})
                if res.get("success"):
                    calculation_results.append(res)
            else:
                err_msg = f"Calculation '{op}' could not proceed: source numeric value not found."
                tool_results.append({"tool": tool_name, "status": "error", "error": err_msg})

    return {
        "tools_used": tools_used,
        "tool_results": tool_results,
        "retrieved_chunks": retrieved_chunks,
        "metadata_results": metadata_results,
        "calculation_results": calculation_results,
    }


async def synthesize_answer_node(
    state: CopilotAgentState,
    config: RunnableConfig
) -> Dict[str, Any]:
    """Synthesize grounded answer from tool results and retrieved evidence."""
    llm_provider = config.get("configurable", {}).get("llm_provider") or get_llm_provider()
    query = state.get("user_query", "").strip()
    raw_chunks = state.get("retrieved_chunks", [])
    metadata_res = state.get("metadata_results") or {}
    calc_results = state.get("calculation_results", [])
    tools_used = state.get("tools_used", [])

    # Case A: Metadata Query Result
    if "get_document_metadata" in tools_used and metadata_res.get("found"):
        fname = metadata_res.get("filename")
        part = metadata_res.get("part_number") or "N/A"
        rev = metadata_res.get("revision") or "N/A"
        status_val = metadata_res.get("status")
        pages = metadata_res.get("page_count", 0)

        answer = (
            f"According to verified engineering document metadata, document '{fname}' "
            f"(Part Number: {part}) is currently at Revision {rev} with status '{status_val}' "
            f"and contains {pages} pages [C1]."
        )
        citation = {
            "citation_id": "C1",
            "document_id": metadata_res.get("document_id"),
            "filename": fname,
            "page_number": 1,
            "chunk_id": "metadata-record",
            "chunk_index": 0,
            "part_number": part,
            "revision": rev,
            "section": "DOCUMENT METADATA REGISTRY",
            "snippet": f"Filename: {fname} | Part: {part} | Rev: {rev} | Status: {status_val} | Pages: {pages}",
        }
        return {
            "final_answer": answer,
            "citations": [citation],
            "should_abstain": False,
        }

    # Case B: Pure Calculator Query Result (no document search used)
    if "calculate_engineering" in tools_used and not raw_chunks:
        if calc_results:
            calc = calc_results[0]
            answer = f"Using the engineering calculator tool: {calc.get('explanation')}."
            return {
                "final_answer": answer,
                "citations": [],
                "should_abstain": False,
            }
        else:
            return {
                "final_answer": "Calculation could not be performed with the provided parameters.",
                "citations": [],
                "should_abstain": True,
            }

    # Case C: Document Search (with optional Calculation)
    threshold = settings.RAG_RELEVANCE_THRESHOLD
    candidate_hits = [c for c in raw_chunks if c.get("score", 0.0) >= threshold]

    if not candidate_hits:
        return {
            "final_answer": INSUFFICIENT_INFORMATION_MSG,
            "citations": [],
            "should_abstain": True,
        }

    # Convert chunk dicts into SearchResultItem instances for ContextBuilder
    search_items: List[SearchResultItem] = []
    for c in candidate_hits:
        search_items.append(
            SearchResultItem(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                chunk_index=c["chunk_index"],
                page_number=c["page_number"],
                filename=c["filename"],
                document_type=c["document_type"],
                part_number=c["part_number"],
                revision=c["revision"],
                content=c["content"],
                score=c["score"],
                retrieval_mode="hybrid",
                metadata={"section": c.get("section")},
            )
        )

    # Build structured evidence context
    context_str, candidate_citations, citation_map = ContextBuilder.build_context(search_items)
    messages = build_rag_messages(context_str, query)

    # LLM generation
    llm_resp = await llm_provider.generate(messages, temperature=0.0)
    answer_text = llm_resp.content.strip()

    # Check abstention
    is_insufficient = (
        INSUFFICIENT_INFORMATION_MSG.lower() in answer_text.lower()
        or "not contain enough information" in answer_text.lower()
        or "insufficient information" in answer_text.lower()
    )

    if is_insufficient:
        return {
            "final_answer": INSUFFICIENT_INFORMATION_MSG,
            "citations": [],
            "should_abstain": True,
        }

    # If calculation was performed in addition to search, append calculated explanation
    if calc_results:
        calc = calc_results[0]
        answer_text += (
            f"\nUsing the engineering conversion tool, this corresponds to approximately "
            f"{calc.get('result')} {calc.get('unit')} ({calc.get('explanation')})."
        )

    # Extract active citations referenced in the answer
    cited_ids = set(re.findall(r"\[(C\d+)\]", answer_text))
    active_citations: List[Dict[str, Any]] = []
    for cid in sorted(cited_ids):
        if cid in citation_map:
            cit_item: CitationItem = citation_map[cid]
            active_citations.append(cit_item.model_dump())

    if not active_citations and candidate_citations:
        active_citations = [candidate_citations[0].model_dump()]

    return {
        "final_answer": answer_text,
        "citations": active_citations,
        "should_abstain": False,
    }
