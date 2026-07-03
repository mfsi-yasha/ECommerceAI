"""
LangChain Tools for the E-Commerce AI Agent.

These tools are called autonomously by the LLM when it needs to perform
specific actions like searching for products or calculating prices.
"""
import logging
import math
from functools import lru_cache

from langchain_core.tools import tool

from .clients import qdrant_client as qdrant
from .clients import postgres_client as postgres

logger = logging.getLogger(__name__)

_embedding_model = None


def _get_embedding_model():
    """Lazy-load the sentence-transformer embedding model (cached after first call)."""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        from .hardware import get_device
        from .config import EMBEDDING_MODEL

        device = get_device()
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL, device=device)
        logger.info(f"Loaded embedding model '{EMBEDDING_MODEL}' on {device}")
    return _embedding_model


@lru_cache(maxsize=128)
def _embed_text(text: str) -> list[float]:
    """Encode a text string into a dense vector, cached for performance."""
    model = _get_embedding_model()
    return model.encode(text).tolist()


@tool
def product_search_tool(
    query: str,
    brand: str = "",
    product_type: str = "",
    subtype: str = "",
    min_price: float = 0,
    max_price: float = 0,
) -> str:
    """Search the product catalog for items matching the query.
    Use this tool whenever the user asks about products, shopping, or recommendations.

    Args:
        query: The natural language search query describing what the user wants.
        brand: Optional brand filter (e.g. 'Apple', 'Samsung', 'Nike'). Leave empty if not specified.
        product_type: Optional broad category filter (e.g. 'Electronics', 'Apparel'). Leave empty if not specified.
        subtype: Optional sub-category filter (e.g. 'Mobile', 'Laptop', 'Shirt'). Leave empty if not specified.
        min_price: Optional minimum price filter. Use 0 if not specified.
        max_price: Optional maximum price filter. Use 0 if not specified.

    Returns:
        A formatted list of matching products with their details and prices.
    """
    filters: dict = {}
    if brand:
        filters["brand"] = brand
    if product_type:
        filters["type"] = product_type
    if subtype:
        filters["subtype"] = subtype
    if min_price > 0:
        filters["min_price"] = min_price
    if max_price > 0:
        filters["max_price"] = max_price

    logger.info(f"Product search tool called: query='{query}', filters={filters}")

    query_vector = _embed_text(query)

    results = []
    qdrant_success = False

    try:
        qdrant.ensure_collection()
        hits = qdrant.search_products(query_vector, filters, limit=10, offset=0)

        for r in hits:
            payload = r.payload or {}
            results.append({
                "id": int(r.id),
                "name": payload.get("name", ""),
                "type": payload.get("type", ""),
                "subtype": payload.get("subtype", ""),
                "brand": payload.get("brand", ""),
                "price": payload.get("price", ""),
                "score": round(r.score, 4),
            })

        if results:
            qdrant_success = True
            logger.info(f"Qdrant returned {len(results)} products")
        else:
            logger.info("Qdrant returned 0 candidates. Falling back to Postgres.")

    except Exception as e:
        logger.warning(f"Qdrant search failed: {e}. Falling back to Postgres.")

    if not qdrant_success:
        try:
            pg_results = postgres.fetch_products_by_filters(filters, limit=10, offset=0)
            for p in pg_results:
                results.append({
                    "id": p["id"],
                    "name": p["name"],
                    "type": p.get("type", ""),
                    "subtype": p.get("subtype", ""),
                    "brand": "",
                    "price": "",
                })
            logger.info(f"Postgres fallback returned {len(results)} products")
        except Exception as e:
            logger.error(f"Postgres fallback also failed: {e}")

    if not results:
        return "No products found matching your search. Try broadening your criteria."

    lines = []
    for i, p in enumerate(results, 1):
        parts = [f"{p['name']}"]
        if p.get("brand"):
            parts.append(f"by {p['brand']}")
        if p.get("type"):
            sub = f"/{p['subtype']}" if p.get("subtype") else ""
            parts.append(f"({p['type']}{sub})")
        if p.get("price"):
            parts.append(f"- ${p['price']}")
        parts.append(f"[ID:{p['id']}]")
        lines.append(f"{i}. {' '.join(parts)}")

    return f"Found {len(results)} products:\n" + "\n".join(lines)


@tool
def calculator_tool(expression: str) -> str:
    """Evaluate a mathematical expression. Use this for any calculations like
    totals, discounts, tax, comparisons, or unit conversions.

    Args:
        expression: A mathematical expression to evaluate (e.g. '(599 + 799) * 0.85' or '1299 - 1299 * 0.15').

    Returns:
        The numerical result of the expression as a string.
    """
    logger.info(f"Calculator tool called: expression='{expression}'")

    # Allowed names for safe evaluation (no builtins)
    safe_names = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
        "pow": pow,
        "sqrt": math.sqrt,
        "ceil": math.ceil,
        "floor": math.floor,
    }

    try:
        # Safely evaluate the expression without access to builtins
        result = eval(expression, {"__builtins__": {}}, safe_names)
        return str(result)
    except Exception as e:
        return f"Error evaluating expression '{expression}': {e}"
