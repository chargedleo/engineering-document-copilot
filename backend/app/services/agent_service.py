import logging
import time
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_core.runnables import RunnableConfig

from app.schemas.agent import AgentQueryRequest, AgentResponse, ToolExecutionTrace
from app.schemas.rag import CitationItem
from app.services.llm import get_llm_provider
from app.agents.graph import copilot_agent_graph
from app.agents.state import CopilotAgentState

logger = logging.getLogger("engineering_copilot.agent_service")


class AgentService:
    """
    Service layer orchestrating the LangGraph Engineering Copilot Agent workflow.
    Manages dependency injection, execution lifecycle, trace aggregation, and timing.
    """

    @classmethod
    async def run_agent(
        cls,
        db: AsyncSession,
        request: AgentQueryRequest,
    ) -> AgentResponse:
        start_time = time.perf_counter()
        query_clean = request.query.strip()
        if not query_clean:
            raise ValueError("Query cannot be empty or contain only whitespace.")

        llm_provider = get_llm_provider()

        initial_state: CopilotAgentState = {
            "session_id": request.session_id or "default-session",
            "user_query": query_clean,
            "top_k": request.top_k,
            "filters": request.filters.model_dump() if request.filters else None,
            "tool_calls": [],
            "tool_results": [],
            "tools_used": [],
            "retrieved_chunks": [],
            "retrieved_documents": [],
            "citations": [],
            "calculation_results": [],
            "metadata_results": None,
            "final_answer": "",
            "should_abstain": False,
            "error": None,
            "execution_metadata": {},
        }

        config: RunnableConfig = {
            "configurable": {
                "db": db,
                "llm_provider": llm_provider,
            }
        }

        # Execute LangGraph workflow
        final_state: CopilotAgentState = await copilot_agent_graph.ainvoke(initial_state, config=config)
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Construct ToolExecutionTraces
        tool_traces: List[ToolExecutionTrace] = []
        for res in final_state.get("tool_results", []):
            t_name = res.get("tool", "unknown_tool")
            status = res.get("status", "success")
            output_raw = res.get("output")
            error_raw = res.get("error")

            # Format input summary from tool_calls
            input_summary = {}
            for call in final_state.get("tool_calls", []):
                if call.get("tool") == t_name:
                    input_summary = call.get("args", {})
                    break

            output_summary = None
            if isinstance(output_raw, dict):
                # Clean summary omitting heavy raw strings
                output_summary = {k: v for k, v in output_raw.items() if k not in ("hits",)}
                if "hits" in output_raw:
                    output_summary["hits_count"] = len(output_raw["hits"])

            tool_traces.append(
                ToolExecutionTrace(
                    tool_name=t_name,
                    status=status,
                    input_summary=input_summary,
                    output_summary=output_summary,
                    error=error_raw,
                )
            )

        # Parse citations into CitationItem models
        citation_items: List[CitationItem] = []
        for c in final_state.get("citations", []):
            try:
                citation_items.append(CitationItem.model_validate(c))
            except Exception as e:
                logger.warning(f"Could not parse citation item {c}: {e}")

        execution_metadata = {
            "latency_ms": round(elapsed_ms, 2),
            "provider": llm_provider.name,
            "model": llm_provider.model_name,
            "agent": "langgraph_engineering_copilot",
            "tool_calls_count": len(final_state.get("tool_calls", [])),
            "tools_used_count": len(final_state.get("tools_used", [])),
        }

        logger.info(
            f"Agent completed query in {elapsed_ms:.1f}ms | Tools used: {final_state.get('tools_used')} "
            f"| Citations: {len(citation_items)} | Abstain: {final_state.get('should_abstain')}"
        )

        return AgentResponse(
            query=query_clean,
            answer=final_state.get("final_answer", ""),
            citations=citation_items,
            tools_used=final_state.get("tools_used", []),
            should_abstain=final_state.get("should_abstain", False),
            tool_traces=tool_traces,
            metadata=execution_metadata,
        )
