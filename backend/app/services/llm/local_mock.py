import logging
import re
from typing import List, Dict, Optional, Tuple

from app.services.llm.base import BaseLLMProvider, ChatMessage, LLMResponse

logger = logging.getLogger("engineering_copilot.llm.mock")

INSUFFICIENT_INFORMATION_MSG = "The available documents do not contain enough information to answer this question."


class LocalMockChatProvider(BaseLLMProvider):
    """
    Deterministic, offline mock LLM provider for engineering question answering.

    Simulates grounded LLM behavior:
    - Extracts context from messages and strictly verifies evidence before answering.
    - Preserves engineering notation, units, tolerances, part numbers, and revisions.
    - Cites source blocks using citation identifiers (e.g. [C1], [C2]).
    - Abstains with exact standard message when context lacks required facts.
    - Immunized against prompt injection in retrieved document text.
    - Requires zero external dependencies or network credentials.
    """

    def __init__(
        self,
        model_name: str = "mock-engineering-llm-v1",
        custom_overrides: Optional[Dict[str, str]] = None,
    ):
        self._model_name = model_name
        self._custom_overrides = custom_overrides or {}

    @property
    def name(self) -> str:
        return "local_mock"

    @property
    def model_name(self) -> str:
        return self._model_name

    def is_configured(self) -> bool:
        return True

    async def generate(
        self,
        messages: List[ChatMessage],
        temperature: float = 0.0,
        max_tokens: int = 1000,
    ) -> LLMResponse:
        # Extract user question and context block
        user_query = ""
        context_text = ""

        for msg in messages:
            if "<engineering_context>" in msg.content:
                match = re.search(r"<engineering_context>(.*?)</engineering_context>", msg.content, re.DOTALL)
                if match:
                    context_text = match.group(1).strip()

            if msg.role == "user":
                if "Question:" in msg.content:
                    q_part = msg.content.split("Question:", 1)[1]
                    if "\n\nProvide a" in q_part:
                        user_query = q_part.split("\n\nProvide a", 1)[0].strip()
                    else:
                        user_query = q_part.splitlines()[0].strip()
                else:
                    user_query = msg.content.strip()

        # Check for scripted overrides (useful for exact testing scenarios)
        for pattern, scripted_answer in self._custom_overrides.items():
            if pattern.lower() in user_query.lower():
                return LLMResponse(
                    content=scripted_answer,
                    model=self._model_name,
                    provider=self.name,
                )

        # Parse in-context evidence blocks: e.g. "--- [C1] --- ... Content: ..."
        parsed_blocks = self._parse_context_blocks(context_text)

        # Generate grounded answer
        answer = self._synthesize_grounded_answer(user_query, parsed_blocks)

        return LLMResponse(
            content=answer,
            model=self._model_name,
            provider=self.name,
            usage={"prompt_tokens": len(context_text) // 4, "completion_tokens": len(answer) // 4},
        )

    def _parse_context_blocks(self, context_str: str) -> List[Tuple[str, str, Dict[str, str]]]:
        """
        Parse context text into list of (citation_id, content, metadata_dict).
        Format:
        --- [C1] ---
        Document: ...
        Content:
        ...
        """
        blocks: List[Tuple[str, str, Dict[str, str]]] = []
        if not context_str:
            return blocks

        # Split on delimiter
        raw_sections = re.split(r"---\s*\[(C\d+)\]\s*---", context_str)
        # raw_sections[0] is prefix before first [C1], then alternating cid, body
        for i in range(1, len(raw_sections), 2):
            cid = raw_sections[i]
            body = raw_sections[i + 1] if i + 1 < len(raw_sections) else ""

            meta: Dict[str, str] = {}
            content = body
            if "Content:" in body:
                meta_part, content_part = body.split("Content:", 1)
                content = content_part.strip()
                for line in meta_part.splitlines():
                    for item in line.split("|"):
                        if ":" in item:
                            k, v = item.split(":", 1)
                            meta[k.strip().lower()] = v.strip()

            blocks.append((cid, content, meta))

        return blocks

    def _synthesize_grounded_answer(
        self,
        query: str,
        blocks: List[Tuple[str, str, Dict[str, str]]]
    ) -> str:
        """Evaluate evidence against query and synthesize grounded response."""
        q_lower = query.lower()

        if not blocks:
            return INSUFFICIENT_INFORMATION_MSG

        # Question 1: Working / Discharge Pressure
        if any(term in q_lower for term in ("working pressure", "discharge pressure", "maximum pressure", "design pressure")):
            for cid, content, meta in blocks:
                match = re.search(r"(?:maximum\s+working|discharge|maximum|nominal|design)\s+pressure[:\s]+([^\n]+)", content, re.IGNORECASE)
                if match:
                    val = match.group(1).strip().rstrip(".")
                    part = meta.get("part") or "the equipment"
                    return f"The maximum working pressure for {part} is {val} [{cid}]."

        # Question 2: Radial Bearing Journal Tolerance
        if any(term in q_lower for term in ("radial bearing", "journal tolerance", "bearing tolerance", "bearing journal")):
            for cid, content, meta in blocks:
                match = re.search(r"Radial bearing journal tolerance:\s*([^\n]+)", content, re.IGNORECASE)
                if match:
                    val = match.group(1).strip().rstrip(".")
                    return f"The radial bearing journal tolerance is {val} [{cid}]."

        # Question 3: Oil Change / Maintenance Interval
        if any(term in q_lower for term in ("oil change", "lubrication interval", "maintenance interval", "change interval", "change frequency")):
            for cid, content, meta in blocks:
                match = re.search(r"Oil change (?:frequency|interval):\s*([^\n]+)", content, re.IGNORECASE)
                if match:
                    val = match.group(1).strip().rstrip(".")
                    return f"The recommended oil change interval is {val} [{cid}]."

        # Question 4: Hydrostatic Test Pressure
        if any(term in q_lower for term in ("hydrostatic test", "hydro test", "test pressure")):
            for cid, content, meta in blocks:
                match = re.search(r"TEST PRESSURE:\s*([^\n]+)", content, re.IGNORECASE)
                if match:
                    val = match.group(1).strip().rstrip(".")
                    return f"The hydrostatic test pressure is {val} [{cid}]."
                match2 = re.search(r"Hydrostatic shell test at\s*([^\n]+)", content, re.IGNORECASE)
                if match2:
                    val = match2.group(1).strip().rstrip(".")
                    return f"The hydrostatic test pressure is {val} [{cid}]."

        # Question 5: Shaft runout
        if "shaft runout" in q_lower:
            for cid, content, meta in blocks:
                match = re.search(r"shaft runout[^\n:]*:\s*([^\n]+)", content, re.IGNORECASE)
                if match:
                    val = match.group(1).strip().rstrip(".")
                    return f"The shaft runout tolerance is {val} [{cid}]."

        # Question 6: Bolt Torque
        if any(term in q_lower for term in ("torque", "bolt torque", "flange bolt")):
            for cid, content, meta in blocks:
                match = re.search(r"([A-Za-z0-9\s\-_]+(?:bolt|torque)[^\.\n]*:\s*\d+\s*Nm[^\.\n]*)", content, re.IGNORECASE)
                if match:
                    val = match.group(1).strip()
                    return f"The specified bolt torque is {val} [{cid}]."

        # General keyword matching fallback across retrieved blocks
        # Only answer if there is high-confidence overlap of technical terms
        # Otherwise strictly abstain
        all_words = set(re.findall(r"\b[A-Za-z0-9_-]{3,}\b", q_lower))
        stop_words = {"what", "is", "the", "of", "for", "in", "at", "to", "a", "an", "and", "or", "how", "why", "does", "do", "can", "could", "should", "would", "which", "are", "be"}
        query_terms = {w for w in all_words if w not in stop_words}

        best_block = None
        best_overlap = 0

        for cid, content, meta in blocks:
            content_lower = content.lower()
            overlap = sum(1 for t in query_terms if t in content_lower)
            if overlap > best_overlap:
                best_overlap = overlap
                best_block = (cid, content, meta)

        # If significant proportion of technical terms match
        if best_block and len(query_terms) > 0 and (best_overlap / len(query_terms) >= 0.75):
            cid, content, meta = best_block
            # Find the most relevant sentence in content
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if s.strip()]
            for s in sentences:
                s_lower = s.lower()
                if sum(1 for t in query_terms if t in s_lower) >= max(2, best_overlap - 1):
                    # Clean prompt injections if present inside sentence
                    clean_s = re.sub(r"IGNORE PREVIOUS INSTRUCTIONS[^\.]*", "", s, flags=re.IGNORECASE).strip()
                    if clean_s:
                        return f"{clean_s} [{cid}]"

        # If no fact directly supports the answer, abstain
        return INSUFFICIENT_INFORMATION_MSG
