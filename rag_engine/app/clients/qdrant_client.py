import logging
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue, Range,
)
from ..config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION, EMBEDDING_DIM

logger = logging.getLogger(__name__)

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Lazy-initialise and return the singleton Qdrant client."""
    global _client
    if _client is None:
        _client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT, timeout=30)
        logger.info(f"Connected to Qdrant at {QDRANT_HOST}:{QDRANT_PORT}")
    return _client


def ensure_collection() -> bool:
    """Create the products collection if it doesn't already exist."""
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )
        logger.info(f"Created Qdrant collection '{QDRANT_COLLECTION}' (dim={EMBEDDING_DIM})")
    return True


def search_products(
    query_vector: list[float],
    filters: dict,
    limit: int = 30,
    offset: int = 0,
) -> list:
    """
    Semantic search with optional payload filters (brand, type, subtype, price).
    Returns a list of ScoredPoint objects.
    """
    client = get_qdrant_client()

    # Build filter conditions from parsed query filters
    must_conditions: list = []

    if filters.get("brand"):
        must_conditions.append(
            FieldCondition(key="brand", match=MatchValue(value=filters["brand"].lower()))
        )

    if filters.get("type"):
        must_conditions.append(
            FieldCondition(key="type", match=MatchValue(value=filters["type"]))
        )

    if filters.get("subtype"):
        must_conditions.append(
            FieldCondition(key="subtype", match=MatchValue(value=filters["subtype"]))
        )

    if filters.get("min_price") is not None or filters.get("max_price") is not None:
        range_kwargs: dict = {}
        if filters.get("min_price") is not None:
            range_kwargs["gte"] = float(filters["min_price"])
        if filters.get("max_price") is not None:
            range_kwargs["lte"] = float(filters["max_price"])
        must_conditions.append(
            FieldCondition(key="price", range=Range(**range_kwargs))
        )

    search_filter = Filter(must=must_conditions) if must_conditions else None

    results = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=search_filter,
        limit=limit,
        offset=offset,
        score_threshold=0.3,
        with_payload=True,
    ).points
    return results


def upsert_points(points: list[PointStruct]) -> None:
    """Upsert a batch of points into the products collection."""
    client = get_qdrant_client()
    client.upsert(collection_name=QDRANT_COLLECTION, points=points)


def get_all_point_ids() -> list[int]:
    """Return every point ID currently stored in the collection."""
    client = get_qdrant_client()
    all_ids: list[int] = []
    offset = None
    while True:
        points, next_offset = client.scroll(
            collection_name=QDRANT_COLLECTION,
            limit=100,
            offset=offset,
            with_payload=False,
            with_vectors=False,
        )
        all_ids.extend([p.id for p in points])
        if next_offset is None:
            break
        offset = next_offset
    return all_ids


def delete_points(point_ids: list[int]) -> None:
    """Delete points by their IDs."""
    client = get_qdrant_client()
    client.delete(
        collection_name=QDRANT_COLLECTION,
        points_selector=point_ids,
    )
