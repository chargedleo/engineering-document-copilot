from typing import TypedDict, List, Dict, Any, Optional


class ToolCall(TypedDict, total=False):
    tool: str
    args: Dict[str, Any]


class ToolResult(TypedDict, total=False):
    tool: str
    status: str
    output: Any
    error: Optional[str]


class CopilotAgentState(TypedDict, total=False):
    """
    Typed state representation for LangGraph Engineering Copilot Agent.
    Maintains user query, tool decisions, execution traces, retrieved chunks,
    grounded citations, calculations, and final answer.
    """
    session_id: str
    user_query: str
    top_k: int
    filters: Optional[Dict[str, Any]]

    # Tool calls & execution
    tool_calls: List[Dict[str, Any]]
    tool_results: List[Dict[str, Any]]
    tools_used: List[str]

    # Retrieval outcomes & calculations
    retrieved_chunks: List[Dict[str, Any]]
    retrieved_documents: List[Dict[str, Any]]
    citations: List[Dict[str, Any]]
    calculation_results: List[Dict[str, Any]]
    metadata_results: Optional[Dict[str, Any]]

    # Final response & status
    final_answer: str
    should_abstain: bool
    error: Optional[str]
    execution_metadata: Dict[str, Any]
