import re
from typing import List, Dict, Any, Optional


class AgentPlanner:
    """
    Analyzes user queries to determine required engineering tools and execution order.
    Detects needs for:
    - Document search (specifications, tolerances, limits)
    - Metadata lookups (revision, status, page count)
    - Engineering calculations (unit conversions, percentage deltas)
    - Multi-tool composite workflows
    """

    METADATA_PATTERNS = [
        r"\b(?:what\s+)?revision\b",
        r"\bdocument\s+status\b",
        r"\bpage\s+count\b",
        r"\bfile\s+size\b",
        r"\bwhen\s+was\s+(?:it|this|the\s+document)\s+created\b",
        r"\bmetadata\b",
    ]

    CALCULATION_PATTERNS = [
        (r"\b(?:convert|in|to)\s+psi\b", "bar_to_psi"),
        (r"\b(?:convert|in|to)\s+bar\b", "psi_to_bar"),
        (r"\b(?:convert|in|to)\s+fahrenheit\b", "celsius_to_fahrenheit"),
        (r"\b(?:convert|in|to)\s+celsius\b", "fahrenheit_to_celsius"),
        (r"\b(?:convert|in|to)\s+(?:lpm|liters\s+per\s+minute)\b", "flow_m3h_to_lpm"),
        (r"\b(?:convert|in|to)\s+(?:m3/h|m³/h)\b", "flow_lpm_to_m3h"),
        (r"\b(?:convert|in|to)\s+(?:hp|horsepower)\b", "kw_to_hp"),
        (r"\b(?:convert|in|to)\s+(?:kw|kilowatts)\b", "hp_to_kw"),
        (r"\bpercentage\s+(?:change|difference|delta|increase|decrease)\b", "percentage_change"),
    ]

    PART_NUMBER_PATTERN = r"\b[A-Z]{2,5}-\d{2,4}-[A-Z0-9]+\b"
    FILENAME_PATTERN = r"\b[A-Za-z0-9_\-]+\.pdf\b"

    @classmethod
    def plan(
        cls,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        q_lower = query.strip().lower()
        tool_calls: List[Dict[str, Any]] = []

        # 1. Check for metadata requirements
        is_metadata_query = any(re.search(p, q_lower) for p in cls.METADATA_PATTERNS)

        # 2. Check for calculation requirements
        calc_op = None
        for pattern, op in cls.CALCULATION_PATTERNS:
            if re.search(pattern, q_lower):
                calc_op = op
                break

        # Check if direct numeric values exist in the prompt for calculation
        direct_numbers = re.findall(r"[-+]?\d*\.?\d+", query)

        # Extract potential identifiers
        part_match = re.search(cls.PART_NUMBER_PATTERN, query, re.IGNORECASE)
        part_number = part_match.group(0).upper() if part_match else (filters.get("part_number") if filters else None)

        file_match = re.search(cls.FILENAME_PATTERN, query, re.IGNORECASE)
        filename = file_match.group(0) if file_match else None

        # Routing Logic:
        # Case A: Pure calculation query (e.g., "convert 16 bar to psi")
        if calc_op and len(direct_numbers) >= 1 and not any(k in q_lower for k in ("what is the", "manual", "spec", "drawing", "pressure of", "tolerance of")):
            val1 = float(direct_numbers[0])
            val2 = float(direct_numbers[1]) if len(direct_numbers) > 1 and calc_op == "percentage_change" else None
            tool_calls.append({
                "tool": "calculate_engineering",
                "args": {
                    "operation": calc_op,
                    "value": val1,
                    "value2": val2,
                }
            })
            return tool_calls

        # Case B: Metadata query
        if is_metadata_query:
            tool_calls.append({
                "tool": "get_document_metadata",
                "args": {
                    "part_number": part_number,
                    "filename": filename,
                }
            })
            # Also include search if part number or filename is unknown, to ground document identity
            if not part_number and not filename:
                tool_calls.insert(0, {
                    "tool": "search_engineering_documents",
                    "args": {"query": query, "top_k": 3}
                })
            return tool_calls

        # Case C: Technical Question with Calculation (e.g., "What is the working pressure in psi?")
        if calc_op:
            # Need search first to find the engineering value, then calculate
            tool_calls.append({
                "tool": "search_engineering_documents",
                "args": {
                    "query": query,
                    "top_k": 5,
                    "part_number": part_number,
                }
            })
            tool_calls.append({
                "tool": "calculate_engineering",
                "args": {
                    "operation": calc_op,
                    # Value will be extracted dynamically from search result
                    "value": None,
                }
            })
            return tool_calls

        # Case D: Default Engineering Specification Query (e.g., running clearances, test pressure, yield strength)
        tool_calls.append({
            "tool": "search_engineering_documents",
            "args": {
                "query": query,
                "top_k": 5,
                "part_number": part_number,
            }
        })
        return tool_calls
