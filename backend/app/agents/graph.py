"""
LangGraph Multi-Tool Engineering Copilot Workflow Definition.

Workflow Topology:
       START
         ↓
  classify_and_plan
   ├── (tools needed) ──→ execute_tools ──→ synthesize_answer ──→ END
   └── (direct/empty) ────────────────────→ synthesize_answer ──→ END
"""

import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph

from app.agents.state import CopilotAgentState
from app.agents.nodes import (
    classify_and_plan_node,
    execute_tools_node,
    synthesize_answer_node,
)

logger = logging.getLogger("engineering_copilot.agents.graph")


def route_after_planning(state: CopilotAgentState) -> str:
    """Conditional router determining whether tool execution is required."""
    tool_calls = state.get("tool_calls", [])
    if tool_calls:
        return "execute_tools"
    return "synthesize_answer"


def build_copilot_graph() -> CompiledStateGraph:
    """Construct and compile the LangGraph state machine for Engineering Copilot."""
    builder = StateGraph(CopilotAgentState)

    # Register Nodes
    builder.add_node("classify_and_plan", classify_and_plan_node)
    builder.add_node("execute_tools", execute_tools_node)
    builder.add_node("synthesize_answer", synthesize_answer_node)

    # Register Edges & Conditional Routing
    builder.add_edge(START, "classify_and_plan")
    builder.add_conditional_edges(
        "classify_and_plan",
        route_after_planning,
        {
            "execute_tools": "execute_tools",
            "synthesize_answer": "synthesize_answer",
        },
    )
    builder.add_edge("execute_tools", "synthesize_answer")
    builder.add_edge("synthesize_answer", END)

    compiled_graph = builder.compile()
    logger.info("Compiled LangGraph Engineering Copilot workflow graph.")
    return compiled_graph


# Global compiled workflow graph instance
copilot_agent_graph = build_copilot_graph()
