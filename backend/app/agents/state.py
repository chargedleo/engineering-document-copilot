from typing import TypedDict, List, Dict, Any, Optional


class CopilotAgentState(TypedDict, total=False):
    """
    Typed state representation for LangGraph multi-agent orchestration.
    Maintains user query, retrieved document chunks, CAD nodes, and synthesized answers.
    """
    session_id: str
    user_query: str
    document_ids: Optional[List[str]]
    include_cad_context: bool

    # Retrieval outcomes
    retrieved_documents: List[Dict[str, Any]]
    retrieved_cad_metadata: List[Dict[str, Any]]

    # Agent reasoning steps & citations
    reasoning_traces: List[str]
    citations: List[Dict[str, Any]]
    cad_references: List[Dict[str, Any]]

    # Final response
    final_answer: str
    error: Optional[str]
