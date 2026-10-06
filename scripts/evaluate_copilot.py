#!/usr/bin/env python3
"""
Engineering Document Intelligence & CAD Knowledge Copilot
Deterministic System Evaluation Suite (Milestone 10)

Evaluates the end-to-end engineering copilot against a curated benchmark
covering factual retrieval, unit conversion, metadata lookup, tolerancing,
grounding with citations, multi-tool chaining, and out-of-domain abstention.

Supports both:
  --mode local : Hermetic in-memory execution with deterministic local providers (Default)
  --mode azure : Live Azure OpenAI + Azure AI Search + Azure PostgreSQL execution
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Any, Optional

# Setup root and backend imports
ROOT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = ROOT_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Suppress engine verbose logs
logging.basicConfig(level=logging.ERROR)
for name in ("sqlalchemy.engine", "sqlalchemy.pool", "sqlalchemy.dialects", "httpx"):
    logging.getLogger(name).setLevel(logging.ERROR)


@dataclass
class EvalTestCase:
    case_id: str
    category: str
    query: str
    expected_tools: List[str]
    expected_abstain: bool
    requires_citation: bool
    expected_snippets: List[str]
    forbidden_snippets: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class EvalTestResult:
    case_id: str
    category: str
    query: str
    passed: bool
    latency_ms: float
    actual_tools: List[str]
    actual_abstain: bool
    citation_count: int
    tool_match: bool
    abstain_match: bool
    citation_match: bool
    grounding_match: bool
    failure_reasons: List[str]
    answer_preview: str


CURATED_BENCHMARK_CASES: List[EvalTestCase] = [
    EvalTestCase(
        case_id="EVAL-A",
        category="Factual Retrieval & Unit Conversion",
        query="What is the maximum working pressure of CFP-402-316L in psi?",
        expected_tools=["search_engineering_documents", "calculate_engineering"],
        expected_abstain=False,
        requires_citation=True,
        expected_snippets=["16.0 bar", "232"],
        description="Retrieves 16.0 bar from Page 1 and dynamically converts to approximately 232.06 psi.",
    ),
    EvalTestCase(
        case_id="EVAL-B",
        category="Deterministic Engineering Calculation",
        query="Convert 75 kW to horsepower",
        expected_tools=["calculate_engineering"],
        expected_abstain=False,
        requires_citation=False,
        expected_snippets=["100.58"],
        description="Executes pure mathematical calculation tool without document search hallucination.",
    ),
    EvalTestCase(
        case_id="EVAL-C",
        category="Document Metadata Registry",
        query="What is the revision of the CFP-402-316L document?",
        expected_tools=["get_document_metadata"],
        expected_abstain=False,
        requires_citation=True,
        expected_snippets=["Revision D"],
        description="Performs relational metadata query against database document registry.",
    ),
    EvalTestCase(
        case_id="EVAL-D",
        category="Engineering Detail & Tolerancing",
        query="What is the radial bearing journal tolerance for CFP-402-316L?",
        expected_tools=["search_engineering_documents"],
        expected_abstain=False,
        requires_citation=True,
        expected_snippets=["ISO h6"],
        description="Retrieves precision engineering tolerance specification with exact bounds from Page 2.",
    ),
    EvalTestCase(
        case_id="EVAL-E",
        category="Out-of-Domain Abstention",
        query="Give me the material specification for a titanium wing spar.",
        expected_tools=["search_engineering_documents"],
        expected_abstain=True,
        requires_citation=False,
        expected_snippets=["not contain enough information"],
        forbidden_snippets=["titanium", "wing spar specification"],
        description="Detects insufficient document evidence on aerospace queries and strictly abstains.",
    ),
    EvalTestCase(
        case_id="EVAL-F",
        category="Multi-Step Composite Tool Chaining",
        query="What is the working pressure in psi?",
        expected_tools=["search_engineering_documents", "calculate_engineering"],
        expected_abstain=False,
        requires_citation=True,
        expected_snippets=["16.0 bar", "232"],
        description="Chains search retrieval into calculation tool and synthesizes answer with citation.",
    ),
    EvalTestCase(
        case_id="EVAL-G",
        category="Document Grounding & Citation Provenance",
        query="What is the recommended oil change frequency for CFP-402-316L?",
        expected_tools=["search_engineering_documents"],
        expected_abstain=False,
        requires_citation=True,
        expected_snippets=["4000"],
        description="Verifies in-text citation linking to Page 2 maintenance interval specification.",
    ),
    EvalTestCase(
        case_id="EVAL-H",
        category="Missing Information Abstention",
        query="What is the return policy and refund procedure for this pump?",
        expected_tools=["search_engineering_documents"],
        expected_abstain=True,
        requires_citation=False,
        expected_snippets=["not contain enough information"],
        forbidden_snippets=["refund within", "return policy"],
        description="Refuses to hallucinate commercial return policies absent from technical pump datasheets.",
    ),
]


async def setup_local_environment():
    """Initializes a hermetic in-memory SQLite database and indexes sample pump specification."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy.pool import StaticPool
    from app.models.base import Base
    from app.services.document_service import DocumentService
    from app.services.embeddings.factory import reset_embedding_provider
    from app.services.search.factory import reset_search_index
    from app.services.llm.factory import reset_llm_provider

    reset_embedding_provider()
    reset_search_index()
    reset_llm_provider()

    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    pdf_path = ROOT_DIR / "data" / "sample_pump_spec.pdf"
    if not pdf_path.exists():
        raise FileNotFoundError(f"Benchmark source PDF not found at {pdf_path}")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    async with session_factory() as session:
        doc, _ = await DocumentService.process_and_store_document(
            db=session,
            file_bytes=pdf_bytes,
            original_filename="sample_pump_spec.pdf",
            document_type="SPECIFICATION",
            part_number="CFP-402-316L",
            revision="D",
        )
        await DocumentService.generate_document_chunks(session, doc.id)

    return session_factory, "Local In-Memory SQLite (Mock LLM + BM25/Vector RRF)"


async def setup_azure_environment():
    """Binds to live Azure cloud services using credentials in backend/.env.azure."""
    env_path = BACKEND_DIR / ".env.azure"
    if not env_path.exists():
        raise FileNotFoundError(f"Azure configuration file not found at {env_path}")

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

    os.environ["EMBEDDING_PROVIDER"] = "azure"
    os.environ["SEARCH_PROVIDER"] = "azure"
    os.environ["LLM_PROVIDER"] = "azure"
    os.environ["STORAGE_PROVIDER"] = "azure"

    from app.core.config import settings
    for key, val in os.environ.items():
        if hasattr(settings, key):
            if key == "DEBUG":
                setattr(settings, key, str(val).lower() in ("true", "1", "yes"))
            else:
                setattr(settings, key, val)

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from app.services.embeddings.factory import reset_embedding_provider
    from app.services.search.factory import reset_search_index
    from app.services.llm.factory import reset_llm_provider

    reset_embedding_provider()
    reset_search_index()
    reset_llm_provider()

    engine = create_async_engine(
        str(settings.DATABASE_URL),
        echo=False,
        future=True,
        pool_pre_ping=True,
    )
    session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    return session_factory, "Live Azure Cloud Stack (OpenAI gpt-4o + AI Search + PostgreSQL)"


async def evaluate_single_case(
    session_factory,
    case: EvalTestCase,
) -> EvalTestResult:
    """Executes a single benchmark test case and evaluates all assertions."""
    from app.schemas.agent import AgentQueryRequest
    from app.services.agent_service import AgentService

    t0 = time.perf_counter()
    req = AgentQueryRequest(query=case.query, top_k=5)

    async with session_factory() as session:
        response = await AgentService.run_agent(session, req)

    latency_ms = (time.perf_counter() - t0) * 1000.0

    actual_tools = list(response.tools_used or [])
    actual_abstain = bool(response.should_abstain)
    citation_count = len(response.citations or [])
    answer = response.answer or ""

    # Assertion 1: Tool Selection
    tool_match = all(tool in actual_tools for tool in case.expected_tools)

    # Assertion 2: Abstention Status
    abstain_match = actual_abstain == case.expected_abstain

    # Assertion 3: Citation Fidelity
    if case.requires_citation:
        citation_match = citation_count >= 1
    else:
        # If abstaining, must not cite fake evidence
        citation_match = (citation_count == 0) if case.expected_abstain else True

    # Assertion 4: Grounding & Snippets
    grounding_match = True
    failure_reasons = []

    if not tool_match:
        missing = [t for t in case.expected_tools if t not in actual_tools]
        failure_reasons.append(f"Missing expected tools: {missing} (called: {actual_tools})")

    if not abstain_match:
        failure_reasons.append(f"Expected abstain={case.expected_abstain}, got {actual_abstain}")

    if not citation_match:
        failure_reasons.append(f"Citation mismatch (count={citation_count}, requires_citation={case.requires_citation})")

    for snippet in case.expected_snippets:
        if snippet.lower() not in answer.lower():
            grounding_match = False
            failure_reasons.append(f"Answer missing expected text: '{snippet}'")

    for forbidden in case.forbidden_snippets:
        if forbidden.lower() in answer.lower():
            grounding_match = False
            failure_reasons.append(f"Answer contains forbidden hallucinated phrase: '{forbidden}'")

    passed = tool_match and abstain_match and citation_match and grounding_match

    return EvalTestResult(
        case_id=case.case_id,
        category=case.category,
        query=case.query,
        passed=passed,
        latency_ms=latency_ms,
        actual_tools=actual_tools,
        actual_abstain=actual_abstain,
        citation_count=citation_count,
        tool_match=tool_match,
        abstain_match=abstain_match,
        citation_match=citation_match,
        grounding_match=grounding_match,
        failure_reasons=failure_reasons,
        answer_preview=answer[:120].replace("\n", " ").strip(),
    )


async def run_evaluation(mode: str = "local", output_json: Optional[str] = None, verbose: bool = False):
    print("=" * 88)
    print("  ENGINEERING COPILOT — BENCHMARK EVALUATION HARNESS")
    print("=" * 88)

    t_start = time.perf_counter()
    if mode == "azure":
        print("  Configuring Live Azure Cloud Execution Mode...")
        session_factory, env_label = await setup_azure_environment()
    else:
        print("  Configuring Local Hermetic Execution Mode...")
        session_factory, env_label = await setup_local_environment()

    print(f"  Execution Target: {env_label}")
    print(f"  Benchmark Cases : {len(CURATED_BENCHMARK_CASES)} curated engineering questions")
    print("=" * 88)
    print()

    results: List[EvalTestResult] = []

    # Run benchmark cases sequentially
    for case in CURATED_BENCHMARK_CASES:
        res = await evaluate_single_case(session_factory, case)
        results.append(res)
        status_tag = "[PASS]" if res.passed else "[FAIL]"
        tools_str = ",".join(res.actual_tools) if res.actual_tools else "none"
        print(f"  {status_tag} {res.case_id:<7} | {res.category[:30]:<30} | {res.latency_ms:6.1f}ms | Tools: {tools_str}")
        if verbose or not res.passed:
            print(f"          Query   : {res.query}")
            print(f"          Answer  : {res.answer_preview}...")
            if res.failure_reasons:
                for reason in res.failure_reasons:
                    print(f"          [FAIL DETAIL] {reason}")
            print()

    t_total = time.perf_counter() - t_start

    # Compute aggregate metrics
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    failed = total - passed
    pass_rate = (passed / total) * 100.0

    abstention_cases = [r for r in results if "Abstention" in r.category]
    abstention_correct = sum(1 for r in abstention_cases if r.abstain_match and r.passed)
    abstention_rate = (abstention_correct / len(abstention_cases)) * 100.0 if abstention_cases else 100.0

    citation_required_cases = [r for r in results if not r.actual_abstain and "Calculation" not in r.category]
    citation_correct = sum(1 for r in citation_required_cases if r.citation_count >= 1)
    citation_rate = (citation_correct / len(citation_required_cases)) * 100.0 if citation_required_cases else 100.0

    tool_correct = sum(1 for r in results if r.tool_match)
    tool_rate = (tool_correct / total) * 100.0

    calc_cases = [r for r in results if "calculate_engineering" in r.actual_tools]
    calc_correct = sum(1 for r in calc_cases if r.grounding_match and r.passed)
    calc_rate = (calc_correct / len(calc_cases)) * 100.0 if calc_cases else 100.0

    latencies = [r.latency_ms for r in results]
    latencies.sort()
    mean_lat = sum(latencies) / len(latencies)
    min_lat = min(latencies)
    max_lat = max(latencies)
    p50_lat = latencies[len(latencies) // 2]

    print("\n" + "=" * 88)
    print("  EVALUATION METRICS & QUALITY REPORT")
    print("=" * 88)
    print(f"  Benchmark Pass Rate           : {passed}/{total} ({pass_rate:.1f}%)")
    print(f"  Abstention Precision & Recall  : {abstention_correct}/{len(abstention_cases)} ({abstention_rate:.1f}%)")
    print(f"  Grounded Citation Fidelity     : {citation_correct}/{len(citation_required_cases)} ({citation_rate:.1f}%)")
    print(f"  Tool Selection Accuracy        : {tool_correct}/{total} ({tool_rate:.1f}%)")
    print(f"  Deterministic Calculation Rate : {calc_correct}/{len(calc_cases)} ({calc_rate:.1f}%)")
    print("-" * 88)
    print(f"  Latency Profile ({mode.upper()})        : Mean={mean_lat:.1f}ms | P50={p50_lat:.1f}ms | Min={min_lat:.1f}ms | Max={max_lat:.1f}ms")
    print(f"  Total Suite Wall Time          : {t_total:.2f}s")
    print("=" * 88)

    # Optional JSON serialization
    if output_json:
        out_path = Path(output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        report_data = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "mode": mode,
            "environment": env_label,
            "total_cases": total,
            "passed": passed,
            "failed": failed,
            "pass_rate_pct": pass_rate,
            "abstention_accuracy_pct": abstention_rate,
            "citation_fidelity_pct": citation_rate,
            "tool_selection_accuracy_pct": tool_rate,
            "calculation_accuracy_pct": calc_rate,
            "latency_metrics": {
                "mean_ms": round(mean_lat, 2),
                "p50_ms": round(p50_lat, 2),
                "min_ms": round(min_lat, 2),
                "max_ms": round(max_lat, 2),
            },
            "results": [asdict(r) for r in results],
        }
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        print(f"\n[+] Detailed evaluation report saved to {out_path}")

    return 0 if failed == 0 else 1


def main():
    parser = argparse.ArgumentParser(description="Evaluate Engineering Copilot Benchmark Suite")
    parser.add_argument("--mode", choices=["local", "azure"], default="local", help="Execution mode (local or azure)")
    parser.add_argument("--output-json", type=str, default=None, help="Save evaluation report to JSON file")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print verbose query and answer details")
    args = parser.parse_args()

    exit_code = asyncio.run(run_evaluation(mode=args.mode, output_json=args.output_json, verbose=args.verbose))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
