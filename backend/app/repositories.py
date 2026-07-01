from sqlalchemy.orm import Session
from .models import ChatHistory, RoleEnum, Product, ProductMetadata

class ECommerceRepository:
    """
    Repository class for handling database operations related to chat history and products.
    """
    def __init__(self, db: Session):
        self.db = db

    def add_chat_message(self, session_id: int, role: str, message: str) -> ChatHistory:
        """
        Adds a new chat message to the database for a specific session.
        """
        try:
            chat = ChatHistory(
                session_id=session_id,
                role=RoleEnum(role),
                message=message
            )
            self.db.add(chat)
            self.db.commit()
            self.db.refresh(chat)
            return chat
        except Exception as e:
            self.db.rollback()
            raise RuntimeError(f"Database error while adding chat message: {e}")
    
    def get_chat_history(self, session_id: str):
        """
        Retrieves the complete chat history for a given session, ordered by timestamp.
        """
        try:
            history = self.db.query(ChatHistory).filter(ChatHistory.session_id == session_id).order_by(ChatHistory.timestamp.asc()).all()
            return [{"role": msg.role.value, "message": msg.message} for msg in history]
        except Exception as e:
            raise RuntimeError(f"Database error while fetching chat history: {e}")
    
    def _format_products(self, products):
        """
        Helper method to format raw database product objects into dictionaries.
        """
        result = []
        for p in products:
            meta = {m.meta_key: m.meta_value for m in p.metadata_items}
            result.append({
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "subtype": p.subtype,
                "metadata": meta
            })
        return result

    def fetch_product_list(self, skip: int = 0, limit: int = 5):
        """
        Fetches a paginated list of products from the database.
        """
        try:
            products = self.db.query(Product).order_by(Product.id).offset(skip).limit(limit).all()
            return self._format_products(products)
        except Exception as e:
            raise RuntimeError(f"Database error while fetching product list: {e}")
        
    def fetch_product_by_ids(self, product_ids: list[int]):
        """
        Fetches a specific list of products by their unique identifiers.
        """
        try:
            products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
            return self._format_products(products)
        except Exception as e:
            raise RuntimeError(f"Database error while fetching products by IDs: {e}")
