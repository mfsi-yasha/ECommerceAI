"""
Vector Delta-Sync Script
========================
Synchronises product data from PostgreSQL → Qdrant.

  - Fetches all products + metadata from Postgres
  - Embeds each product's text representation
  - Compares against existing Qdrant points using content hashes
  - Upserts new/changed vectors, deletes stale ones

Usage:
    Local:  make sync-vectors          (runs with POSTGRES_HOST=localhost)
    Docker: docker exec ecommerce_rag_engine python scripts/sync_vectors.py
"""
import sys
import os
import hashlib
import logging
import time

# Allow importing from the app package when run as a standalone script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [SYNC] %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


def build_product_text(product: dict) -> str:
    """Create a single searchable text string from a product and its metadata."""
    parts = [product["name"]]
    if product.get("type"):
        parts.append(product["type"])
    if product.get("subtype"):
        parts.append(product["subtype"])

    meta = product.get("metadata", {})
    for key in ["brand", "color", "material", "cpu", "ram", "storage"]:
        if key in meta:
            parts.append(f"{key}: {meta[key]}")

    return " ".join(parts)


def compute_hash(text: str) -> str:
    """MD5 hash of the product text for change detection."""
    return hashlib.md5(text.encode()).hexdigest()


def build_payload(product: dict) -> dict:
    """Build the Qdrant point payload with filterable fields."""
    meta = product.get("metadata", {})

    price = None
    if "price" in meta:
        try:
            price = float(meta["price"])
        except (ValueError, TypeError):
            pass

    return {
        "name": product["name"],
        "type": product.get("type", ""),
        "subtype": product.get("subtype", ""),
        "brand": meta.get("brand", "").lower(),
        "price": price,
        "color": meta.get("color", ""),
        "product_id": product["id"],
    }


def sync():
    """Run the full delta-sync pipeline."""
    start = time.time()
    logger.info("Starting vector delta-sync…")

    # ── 1. Load embedding model ──────────────────────────────────────────────
    logger.info("Loading embedding model…")
    from sentence_transformers import SentenceTransformer
    from app.hardware import get_device
    from app.config import EMBEDDING_MODEL

    device = get_device()
    model = SentenceTransformer(EMBEDDING_MODEL, device=device)
    logger.info(f"Embedding model loaded on {device}")

    # ── 2. Fetch products from PostgreSQL ────────────────────────────────────
    from app.clients.postgres_client import fetch_all_products

    logger.info("Fetching products from PostgreSQL…")
    products = fetch_all_products()
    logger.info(f"Found {len(products)} products in PostgreSQL")

    if not products:
        logger.warning("No products found. Run 'make seed' first.")
        return

    # ── 3. Ensure Qdrant collection ──────────────────────────────────────────
    from app.clients.qdrant_client import (
        ensure_collection, upsert_points, get_all_point_ids, delete_points,
        get_qdrant_client,
    )
    from qdrant_client.models import PointStruct

    ensure_collection()

    # ── 4. Determine delta ───────────────────────────────────────────────────
    existing_ids = set(get_all_point_ids())
    postgres_ids = {p["id"] for p in products}

    to_remove = existing_ids - postgres_ids
    logger.info(
        f"Existing vectors: {len(existing_ids)} | "
        f"Postgres products: {len(postgres_ids)} | "
        f"Stale (to remove): {len(to_remove)}"
    )

    # ── 5. Build texts & embeddings ──────────────────────────────────────────
    logger.info("Generating embeddings…")
    texts: list[str] = []
    enriched: list[dict] = []

    for product in products:
        text = build_product_text(product)
        enriched.append({**product, "text": text, "content_hash": compute_hash(text)})
        texts.append(text)

    embeddings = model.encode(texts, show_progress_bar=True)

    # ── 6. Build Qdrant points and upsert ────────────────────────────────────
    points: list[PointStruct] = []
    for i, product in enumerate(enriched):
        payload = build_payload(product)
        payload["content_hash"] = product["content_hash"]

        points.append(
            PointStruct(
                id=product["id"],
                vector=embeddings[i].tolist(),
                payload=payload,
            )
        )

    if points:
        upsert_points(points)
        logger.info(f"Upserted {len(points)} product vectors")

    # ── 7. Remove stale vectors ──────────────────────────────────────────────
    if to_remove:
        delete_points(list(to_remove))
        logger.info(f"Removed {len(to_remove)} stale vectors")

    elapsed = time.time() - start
    logger.info(
        f"✅ Delta-sync complete in {elapsed:.1f}s — "
        f"{len(points)} synced, {len(to_remove)} removed, "
        f"{len(existing_ids & postgres_ids)} previously existing"
    )


if __name__ == "__main__":
    sync()
