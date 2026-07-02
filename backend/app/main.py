"""
FastAPI backend application serving as the API Gateway.
Handles user queries, delegates AI processing to the RAG Engine,
hydrates product data from the database, and manages chat history.
"""
import json
import logging
import os

import httpx
from fastapi import FastAPI, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .repositories import ECommerceRepository
from .schemas import SearchResponse, ChatHistoryResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

RAG_ENGINE_URL = os.getenv("RAG_ENGINE_URL", "http://localhost:8002")

app = FastAPI(title="E-Commerce AI System Gateway")


@app.get("/api/health")
def health_check():
    """Returns a simple status check to confirm the backend is running."""
    return {"status": "healthy"}


@app.get("/api/chat/{session_id}", response_model=ChatHistoryResponse)
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the full chat history for a given session.
    Agent messages are parsed to reconstruct the AI response text
    and hydrate any referenced product IDs into full product objects.
    """
    try:
        repo = ECommerceRepository(db)
        history = repo.get_chat_history(session_id)
        history_out = []

        for msg in history:
            if msg["role"] == "agent":
                try:
                    parsed = json.loads(msg["message"])
                    text = parsed.get("text", msg["message"])
                    p_ids = parsed.get("product_ids", [])
                    products = repo.fetch_product_by_ids(p_ids) if p_ids else []
                    history_out.append({"role": "agent", "message": text, "products": products})
                except Exception:
                    history_out.append({"role": "agent", "message": msg["message"], "products": []})
            else:
                history_out.append({"role": "user", "message": msg["message"]})

        return ChatHistoryResponse(session_id=session_id, history=history_out)
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/search", response_model=SearchResponse)
def search(query: str = Query(...), session_id: str = Query(...), db: Session = Depends(get_db)):
    """
    Processes a user search query through the following steps:
      1. Logs the user query into chat history.
      2. Delegates to the RAG Engine for AI-powered retrieval and response.
      3. Hydrates the returned product IDs into full product objects from Postgres.
      4. Logs the agent response into chat history.
      5. Returns the AI response and hydrated product list.

    If the RAG Engine is unavailable, falls back to returning a generic
    message with a small set of products directly from the database.
    """
    try:
        repo = ECommerceRepository(db)

        # Fetch chat history for context
        history_records = repo.get_chat_history(session_id)
        chat_history = []
        for r in history_records:
            msg_text = r["message"]
            if r["role"] == "agent":
                try:
                    parsed = json.loads(msg_text)
                    msg_text = parsed.get("text", msg_text)
                except Exception:
                    pass
            chat_history.append({"role": "assistant" if r["role"] == "agent" else r["role"], "message": msg_text})
        
        # Log the incoming user message
        repo.add_chat_message(session_id=session_id, role="user", message=query)

        # Delegate to the RAG Engine
        try:
            rag_response = httpx.post(
                f"{RAG_ENGINE_URL}/rag/query",
                json={
                    "query": query, 
                    "session_id": session_id,
                    "chat_history": chat_history
                },
                timeout=httpx.Timeout(connect=5.0, read=120.0, write=5.0, pool=5.0),
            )
            rag_response.raise_for_status()
            rag_data = rag_response.json()

            ai_response_text = rag_data.get("ai_response", "")
            product_ids = rag_data.get("product_ids", [])

        except Exception as e:
            logger.warning(f"RAG Engine unavailable ({e}), using fallback")
            ai_response_text = (
                "I'm having trouble connecting to the AI service right now. "
                "Here are some products you might like:"
            )
            products_fallback = repo.fetch_product_list(limit=5)
            product_ids = [p["id"] for p in products_fallback]

        # Hydrate product IDs into full product objects
        products = repo.fetch_product_by_ids(product_ids) if product_ids else []

        # Log the agent response for chat history replay
        agent_db_msg = json.dumps({"text": ai_response_text, "product_ids": product_ids})
        repo.add_chat_message(session_id=session_id, role="agent", message=agent_db_msg)

        return SearchResponse(ai_response=ai_response_text, products=products)
    except Exception as e:
        logger.error(f"Error processing search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
