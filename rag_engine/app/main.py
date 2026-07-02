import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .graph import build_graph, RAGState
from .clients.llm_client import pull_model, check_model_available
from .clients.qdrant_client import ensure_collection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)

_graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
    global _graph
    logger.info("═══ RAG Engine starting up ═══")

    try:
        ensure_collection()
    except Exception as e:
        logger.warning(f"Qdrant not ready yet: {e} (will retry on first query)")

    if not check_model_available():
        logger.info("LLM model not found on server — pulling now...")
        pull_model()
    else:
        logger.info("LLM model already available.")

    _graph = build_graph()

    logger.info("═══ RAG Engine ready ═══")
    yield
    logger.info("═══ RAG Engine shutting down ═══")


app = FastAPI(title="RAG Engine", lifespan=lifespan)


class RAGQueryRequest(BaseModel):
    """Incoming query from the FastAPI Gateway."""
    query: str
    session_id: str
    chat_history: list[dict] = []

class RAGQueryResponse(BaseModel):
    """
    Strict output boundary: only the AI text + product IDs.
    No full product objects — hydration happens in the Gateway.
    """
    ai_response: str
    product_ids: list[int]


@app.get("/health")
def health_check():
    """Health probe for Docker and the Gateway."""
    return {"status": "healthy", "service": "rag_engine"}

@app.post("/rag/query", response_model=RAGQueryResponse)
def rag_query(request: RAGQueryRequest):
    """
    Process a user query through the LangGraph RAG pipeline.
    Returns {ai_response, product_ids} — nothing more.
    """
    logger.info(f"Incoming query: '{request.query}' (session={request.session_id})")

    if _graph is None:
        raise HTTPException(status_code=503, detail="RAG Engine is still initialising")

    initial_state: RAGState = {
        "query": request.query,
        "session_id": request.session_id,
        "chat_history": request.chat_history,
        "intent": "search",
        "search_query": request.query,
        "filters": {},
        "offset": 0,
        "requested_count": 10,
        "candidate_ids": [],
        "product_context": [],
        "total_matches": 0,
        "product_ids": [],
        "scenario": "",
        "ai_response": "",
    }

    result = _graph.invoke(initial_state)

    logger.info(
        f"Pipeline complete — scenario={result['scenario']}, "
        f"ids={result['product_ids']}"
    )

    return RAGQueryResponse(
        ai_response=result["ai_response"],
        product_ids=result["product_ids"],
    )
