"""
Repository layer for database operations on products and chat history.
Keeps all raw SQL/ORM logic out of the route handlers.
"""
from sqlalchemy.orm import Session

from .models import ChatHistory, Product, RoleEnum


class ECommerceRepository:
    """Encapsulates all database queries for products and chat messages."""

    def __init__(self, db: Session):
        self.db = db

    def add_chat_message(self, session_id: str, role: str, message: str) -> ChatHistory:
        """Inserts a new chat message into the database for the given session."""
        try:
            chat = ChatHistory(
                session_id=session_id,
                role=RoleEnum(role),
                message=message,
            )
            self.db.add(chat)
            self.db.commit()
            self.db.refresh(chat)
            return chat
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Database error while adding chat message: {e}")

    def get_chat_history(self, session_id: str) -> list[dict]:
        """Returns the complete chat history for a session, ordered by timestamp."""
        try:
            history = (
                self.db.query(ChatHistory)
                .filter(ChatHistory.session_id == session_id)
                .order_by(ChatHistory.timestamp.asc())
                .all()
            )
            return [{"role": msg.role.value, "message": msg.message} for msg in history]
        except Exception as e:
            raise RuntimeError(f"Database error while fetching chat history: {e}")

    def _format_products(self, products) -> list[dict]:
        """Converts raw ORM product objects into plain dictionaries."""
        result = []
        for p in products:
            meta = {m.meta_key: m.meta_value for m in p.metadata_items}
            result.append({
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "subtype": p.subtype,
                "metadata": meta,
            })
        return result

    def fetch_product_list(self, skip: int = 0, limit: int = 5) -> list[dict]:
        """Fetches a paginated list of products ordered by ID."""
        try:
            products = self.db.query(Product).order_by(Product.id).offset(skip).limit(limit).all()
            return self._format_products(products)
        except Exception as e:
            raise RuntimeError(f"Database error while fetching product list: {e}")

    def fetch_product_by_ids(self, product_ids: list[int]) -> list[dict]:
        """Fetches specific products by their IDs."""
        try:
            products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
            return self._format_products(products)
        except Exception as e:
            raise RuntimeError(f"Database error while fetching products by IDs: {e}")
