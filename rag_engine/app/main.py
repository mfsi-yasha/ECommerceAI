import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage

from .graph import build_agent
from .clients.llm_client import pull_model, check_model_available
from .clients.qdrant_client import ensure_collection
from .config import LOCAL_MODEL_LABEL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle hook."""
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

    logger.info("═══ RAG Engine ready ═══")
    yield
    logger.info("═══ RAG Engine shutting down ═══")


app = FastAPI(title="RAG Engine", lifespan=lifespan)


class RAGQueryRequest(BaseModel):
    """Incoming query from the FastAPI Gateway."""
    query: str
    session_id: str
    chat_history: list[dict] = []
    llm_provider: str = LOCAL_MODEL_LABEL


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


def _extract_product_ids(text: str) -> list[int]:
    """
    Extract product IDs from the agent's tool output.
    The product_search_tool embeds IDs as [ID:123] in its output.
    """
    import re
    return [int(m) for m in re.findall(r"\[ID:(\d+)\]", text)]


@app.post("/rag/query", response_model=RAGQueryResponse)
def rag_query(request: RAGQueryRequest):
    """
    Process a user query through the ReAct Agent.
    The agent autonomously decides which tools to call.
    Returns {ai_response, product_ids} — nothing more.
    """
    logger.info(
        f"Incoming query: '{request.query}' "
        f"(session={request.session_id}, provider={request.llm_provider})"
    )

    try:
        # Build a fresh agent for the selected provider
        agent = build_agent(request.llm_provider)

        # Convert chat history into LangChain message objects
        messages = []
        for msg in request.chat_history[-6:]:
            content = msg.get("message", "")
            if msg.get("role") in ("user",):
                messages.append(HumanMessage(content=content))
            elif msg.get("role") in ("assistant", "agent"):
                # Truncate long assistant messages for context window efficiency
                if len(content) > 200:
                    content = content[:200] + "... [truncated]"
                messages.append(AIMessage(content=content))

        messages.append(HumanMessage(content=request.query))

        result = agent.invoke({"messages": messages})

        agent_messages = result.get("messages", [])
        ai_response = ""
        all_tool_output = ""

        for msg in agent_messages:
            if hasattr(msg, "type"):
                if msg.type == "ai" and msg.content:
                    ai_response = msg.content
                elif msg.type == "tool" and msg.content:
                    all_tool_output += msg.content + "\n"

        product_ids = _extract_product_ids(all_tool_output)

        if not ai_response:
            ai_response = "I'm here to help with your shopping or any questions you have!"

        import re
        ai_response = re.sub(r"\s*\[ID:\d+\]", "", ai_response).strip()

        logger.info(
            f"Agent complete — product_ids={product_ids}, "
            f"response_preview={ai_response[:100]}..."
        )

        return RAGQueryResponse(
            ai_response=ai_response,
            product_ids=product_ids,
        )

    except Exception as e:
        logger.error(f"Agent execution error: {e}", exc_info=True)

        # Graceful fallback
        return RAGQueryResponse(
            ai_response=(
                "I'm having trouble processing your request right now. "
                "Please try again in a moment!"
            ),
            product_ids=[],
        )
