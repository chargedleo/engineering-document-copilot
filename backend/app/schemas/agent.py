from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.chunk import SearchFilters
from app.schemas.rag import CitationItem


class AgentQueryRequest(BaseModel):
    """Input payload for LangGraph Engineering Copilot Agent query."""
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Technical engineering question, calculation request, or metadata inquiry"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier for conversational tracing"
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum candidate chunks to retrieve during search operations"
    )
    filters: Optional[SearchFilters] = Field(
        default=None,
        description="Optional metadata filters (part_number, revision, document_type, document_id)"
    )


class ToolExecutionTrace(BaseModel):
    """Execution trace of a specific tool invoked by the agent."""
    tool_name: str = Field(..., description="Name of the executed tool")
    status: str = Field(..., description="Status of tool execution ('success' or 'error')")
    input_summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of input parameters passed to tool")
    output_summary: Optional[Dict[str, Any]] = Field(default=None, description="Summary of output returned by tool")
    error: Optional[str] = Field(default=None, description="Error message if tool execution failed")


class AgentResponse(BaseModel):
    """Synthesized response from the LangGraph Engineering Copilot Agent."""
    query: str = Field(..., description="Original user query submitted")
    answer: str = Field(..., description="Grounded technical response synthesized by agent")
    citations: List[CitationItem] = Field(
        default_factory=list,
        description="List of supporting document citations referenced in the answer"
    )
    tools_used: List[str] = Field(
        default_factory=list,
        description="Names of tools genuinely invoked by the agent"
    )
    should_abstain: bool = Field(
        default=False,
        description="Flag indicating whether agent abstained due to missing evidence or scope boundary"
    )
    tool_traces: List[ToolExecutionTrace] = Field(
        default_factory=list,
        description="Structured execution trace of tool calls"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metrics including latency_ms, provider, model, and agent name"
    )
