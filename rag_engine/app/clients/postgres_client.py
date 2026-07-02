import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from ..config import DATABASE_URL

logger = logging.getLogger(__name__)

_engine = None
_SessionLocal = None


def _init_db():
    """Lazy-initialise the SQLAlchemy engine and session factory."""
    global _engine, _SessionLocal
    if _engine is None:
        _engine = create_engine(DATABASE_URL)
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
        logger.info("Connected to PostgreSQL (read-only)")


def get_session():
    """Return a new database session."""
    _init_db()
    return _SessionLocal()


def fetch_all_products() -> list[dict]:
    """
    Fetch every product with its key-value metadata.
    Used by the sync_vectors script to build embeddings.
    """
    session = get_session()
    try:
        result = session.execute(text("""
            SELECT p.id, p.name, p.type, p.subtype,
                   json_agg(
                       json_build_object('key', pm.meta_key, 'value', pm.meta_value)
                   ) AS metadata
            FROM products p
            LEFT JOIN product_metadata pm ON p.id = pm.product_id
            GROUP BY p.id, p.name, p.type, p.subtype
            ORDER BY p.id
        """))
        products = []
        for row in result:
            meta_dict: dict[str, str] = {}
            if row.metadata and isinstance(row.metadata, list):
                for m in row.metadata:
                    if m.get("key"):
                        meta_dict[m["key"]] = m["value"]
            products.append({
                "id": row.id,
                "name": row.name,
                "type": row.type,
                "subtype": row.subtype,
                "metadata": meta_dict,
            })
        return products
    finally:
        session.close()


def fetch_products_by_filters(filters: dict, limit: int = 30, offset: int = 0) -> list[dict]:
    """
    Fallback SQL retrieval when Qdrant returns no results.
    Applies brand, type, subtype, and price-range constraints.
    """
    session = get_session()
    try:
        conditions = ["1=1"]
        params: dict = {}

        if filters.get("type"):
            conditions.append("p.type = :type")
            params["type"] = filters["type"]

        if filters.get("subtype"):
            conditions.append("p.subtype = :subtype")
            params["subtype"] = filters["subtype"]

        if filters.get("brand"):
            conditions.append(
                "EXISTS ("
                "  SELECT 1 FROM product_metadata pm_b"
                "  WHERE pm_b.product_id = p.id"
                "    AND pm_b.meta_key = 'brand'"
                "    AND LOWER(pm_b.meta_value) = LOWER(:brand)"
                ")"
            )
            params["brand"] = filters["brand"]

        if filters.get("min_price") is not None:
            conditions.append(
                "EXISTS ("
                "  SELECT 1 FROM product_metadata pm_lo"
                "  WHERE pm_lo.product_id = p.id"
                "    AND pm_lo.meta_key = 'price'"
                "    AND CAST(pm_lo.meta_value AS FLOAT) >= :min_price"
                ")"
            )
            params["min_price"] = float(filters["min_price"])

        if filters.get("max_price") is not None:
            conditions.append(
                "EXISTS ("
                "  SELECT 1 FROM product_metadata pm_hi"
                "  WHERE pm_hi.product_id = p.id"
                "    AND pm_hi.meta_key = 'price'"
                "    AND CAST(pm_hi.meta_value AS FLOAT) <= :max_price"
                ")"
            )
            params["max_price"] = float(filters["max_price"])

        where_clause = " AND ".join(conditions)
        query = text(
            f"SELECT p.id, p.name, p.type, p.subtype"
            f"  FROM products p"
            f" WHERE {where_clause}"
            f" ORDER BY p.id"
            f" LIMIT :limit OFFSET :offset"
        )
        params["limit"] = limit
        params["offset"] = offset

        result = session.execute(query, params)
        return [
            {"id": row.id, "name": row.name, "type": row.type, "subtype": row.subtype}
            for row in result
        ]
    finally:
        session.close()
