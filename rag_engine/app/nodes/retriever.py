import logging
from ..clients import qdrant_client as qdrant
from ..clients import postgres_client as postgres

logger = logging.getLogger(__name__)

_embedding_model = None


def _get_embedding_model():
    """Lazy-load the sentence-transformer embedding model (cached after first call)."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        from ..hardware import get_device
        from ..config import EMBEDDING_MODEL

        device = get_device()
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=device)
        logger.info(f"Loaded embedding model '{EMBEDDING_MODEL}' on {device}")
    return _embedding_model


def embed_text(text: str) -> list[float]:
    """Encode a text string into a dense vector."""
    model = _get_embedding_model()
    return model.encode(text).tolist()


# ─── LangGraph Node ──────────────────────────────────────────────────────────

def retrieve_products(state: dict) -> dict:
    """
    LangGraph node: Retrieve candidate products.

    1. Embed the user query
    2. Filtered semantic search in Qdrant (primary)
    3. Fallback to Postgres SQL filters if Qdrant throws an error
    """
    query = state["search_query"]
    filters = state["filters"]
    offset = state.get("offset", 0)
    limit = state.get("requested_count", 10) + 10

    # ── Step 1: Embed the search query ───────────────────────────────────────
    query_vector = embed_text(query)

    # ── Step 2: Qdrant semantic + filtered search ────────────────────────────
    candidate_ids: list[int] = []
    product_context: list[dict] = []
    qdrant_success = False

    try:
        qdrant.ensure_collection()
        results = qdrant.search_products(query_vector, filters, limit=30, offset=offset)

        for r in results:
            payload = r.payload or {}
            candidate_ids.append(int(r.id))
            product_context.append({
                "id": int(r.id),
                "name": payload.get("name", ""),
                "type": payload.get("type", ""),
                "subtype": payload.get("subtype", ""),
                "brand": payload.get("brand", ""),
                "price": payload.get("price", ""),
                "score": round(r.score, 4),
            })
            
        if len(candidate_ids) == 0:
            qdrant_success = False
            logger.info("Qdrant returned 0 candidates. Forcing Postgres fallback for generic queries.")
        else:
            qdrant_success = True
            logger.info(f"Qdrant returned {len(candidate_ids)} candidates")

    except Exception as e:
        logger.warning(f"Qdrant search failed: {e}. Falling back to Postgres.")

    # ── Step 3: Postgres fallback (ONLY on error) ────────────────────────────
    if not qdrant_success:
        try:
            pg_results = postgres.fetch_products_by_filters(filters, limit=30, offset=offset)
            for p in pg_results:
                candidate_ids.append(p["id"])
                product_context.append({
                    "id": p["id"],
                    "name": p["name"],
                    "type": p.get("type", ""),
                    "subtype": p.get("subtype", ""),
                    "brand": "",
                    "price": "",
                    "score": 0.0,
                })
            logger.info(f"Postgres fallback returned {len(candidate_ids)} candidates")
        except Exception as e:
            logger.error(f"Postgres fallback also failed: {e}")

    return {
        "candidate_ids": candidate_ids,
        "product_context": product_context,
        "total_matches": len(candidate_ids),
    }
