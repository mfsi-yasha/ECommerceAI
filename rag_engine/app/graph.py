import logging
from typing import TypedDict
from langgraph.graph import StateGraph, END

from .nodes.analyzer import analyze_query
from .nodes.retriever import retrieve_products
from .nodes.ranker import rank_results
from .nodes.responder import respond

logger = logging.getLogger(__name__)


class RAGState(TypedDict):
    """Shared state schema flowing through the RAG pipeline."""
    query: str
    session_id: str
    chat_history: list[dict]
    intent: str
    search_query: str
    filters: dict
    offset: int
    requested_count: int
    candidate_ids: list[int]
    product_context: list[dict]
    total_matches: int
    product_ids: list[int]
    scenario: str
    ai_response: str


def route_after_analysis(state: RAGState) -> str:
    """Conditional edge logic after query analysis."""
    if state.get("intent") == "chat":
        return "respond"
    return "retrieve"


def build_graph():
    """Construct and compile the LangGraph state machine."""
    graph = StateGraph(RAGState)

    # Register nodes
    graph.add_node("analyze", analyze_query)
    graph.add_node("retrieve", retrieve_products)
    graph.add_node("rank", rank_results)
    graph.add_node("respond", respond)

    # Wire the linear pipeline
    graph.set_entry_point("analyze")
    
    # Conditional routing based on intent
    graph.add_conditional_edges(
        "analyze",
        route_after_analysis,
        {
            "retrieve": "retrieve",
            "respond": "respond"
        }
    )
    
    graph.add_edge("retrieve", "rank")
    graph.add_edge("rank", "respond")
    graph.add_edge("respond", END)

    compiled = graph.compile()
    logger.info("LangGraph RAG pipeline compiled: Analyze → [Retrieve → Rank] → Respond")
    return compiled
