"""
SteelMind AI Wizard — LangGraph Pipeline
==========================================
Sequential multi-agent pipeline (fixes INVALID_CONCURRENT_GRAPH_UPDATE).

Pipeline Flow:
    Orchestrator → Vision Agent → RAG Agent → Anomaly Agent
        → Diagnostic Agent → Risk Scorer → Report Generator → END

Vision / RAG / Anomaly agents each skip gracefully when their required
input (image / CSV) is not provided, so the pipeline always completes.
"""

import logging

from langgraph.graph import StateGraph, END

from src.schemas import SteelMindState
from src.agents.orchestrator import execute_orchestration
from src.agents.vision_agent import execute_vision_analysis
from src.agents.rag_agent import execute_rag_retrieval
from src.agents.anomaly_agent import execute_anomaly_check
from src.agents.diagnostic_agent import execute_diagnostic_synthesis
from src.agents.risk_scorer import execute_risk_calculation
from src.agents.report_generator import execute_report_compilation

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════
# Graph Builder
# ══════════════════════════════════════════════════════════════

def build_steelmind_graph() -> StateGraph:
    """
    Build and compile the LangGraph multi-agent pipeline.

    Uses a sequential architecture to avoid LangGraph's
    INVALID_CONCURRENT_GRAPH_UPDATE error, which occurs when parallel
    nodes write to the same shared state keys simultaneously.

    Each data-gathering agent only writes its own dedicated output key
    (vision_output / rag_context / anomaly_result) and skips internally
    when its required input is absent.

    Returns:
        Compiled LangGraph runnable
    """
    graph = StateGraph(SteelMindState)

    # ── Add all agent nodes ──────────────────────
    graph.add_node("orchestrator",     execute_orchestration)
    graph.add_node("vision_agent",     execute_vision_analysis)
    graph.add_node("rag_agent",        execute_rag_retrieval)
    graph.add_node("anomaly_agent",    execute_anomaly_check)
    graph.add_node("diagnostic_agent", execute_diagnostic_synthesis)
    graph.add_node("risk_scorer",      execute_risk_calculation)
    graph.add_node("report_generator", execute_report_compilation)

    # ── Entry point ──────────────────────────────
    graph.set_entry_point("orchestrator")

    # ── Sequential pipeline ───────────────────────
    graph.add_edge("orchestrator",     "vision_agent")
    graph.add_edge("vision_agent",     "rag_agent")
    graph.add_edge("rag_agent",        "anomaly_agent")
    graph.add_edge("anomaly_agent",    "diagnostic_agent")
    graph.add_edge("diagnostic_agent", "risk_scorer")
    graph.add_edge("risk_scorer",      "report_generator")
    graph.add_edge("report_generator", END)

    # ── Compile ───────────────────────────────────
    compiled = graph.compile()
    logger.info("✅ SteelMind LangGraph pipeline compiled successfully")
    return compiled


# ══════════════════════════════════════════════════════════════
# Global Pipeline Instance
# ══════════════════════════════════════════════════════════════

steelmind_pipeline = None


def get_pipeline():
    """
    Get or create the SteelMind pipeline singleton.
    Lazy initialization to avoid import-time side effects.
    """
    global steelmind_pipeline
    if steelmind_pipeline is None:
        steelmind_pipeline = build_steelmind_graph()
    return steelmind_pipeline


async def execute_steelmind_pipeline(initial_state: dict) -> SteelMindState:
    """
    Execute the full SteelMind pipeline with given inputs.

    Args:
        initial_state: Dict with user inputs (query, image_path, csv_path, etc.)

    Returns:
        Final SteelMindState with all agent outputs populated
    """
    pipeline = get_pipeline()

    # Build state with all required fields and correct flags
    state = {
        "query":           initial_state.get("query", ""),
        "language":        initial_state.get("language", "en"),
        "has_image":       bool(initial_state.get("image_path")),
        "has_csv":         bool(initial_state.get("csv_path")),
        "has_docs":        bool(initial_state.get("doc_paths")),
        "image_path":      initial_state.get("image_path"),
        "csv_path":        initial_state.get("csv_path"),
        "doc_paths":       initial_state.get("doc_paths"),
        "equipment_id":    initial_state.get("equipment_id"),
        "equipment_type":  initial_state.get("equipment_type"),
        "session_id":      initial_state.get("session_id", "default"),
        "chat_history":    initial_state.get("chat_history"),
        "vision_output":   None,
        "rag_context":     None,
        "anomaly_result":  None,
        "diagnosis":       None,
        "risk_level":      None,
        "risk_details":    None,
        "report":          None,
        "force_critical":  None,
        "rag_error":       None,
        "pipeline_errors": [],
    }

    logger.info(
        "🚀 Starting SteelMind pipeline | session=%s | has_image=%s | has_csv=%s",
        state["session_id"], state["has_image"], state["has_csv"],
    )

    try:
        result = await pipeline.ainvoke(state)
        logger.info("✅ Pipeline completed | session=%s", state["session_id"])
        return result
    except Exception as e:
        logger.error("❌ Pipeline failed: %s", str(e), exc_info=True)
        state["pipeline_errors"] = [str(e)]
        return state
