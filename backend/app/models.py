from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base
import enum

class RoleEnum(str, enum.Enum):
    """
    Enumeration representing the sender of a chat message.
    Can be either 'user' or 'agent'.
    """
    user = "user"
    agent = "agent"

class Product(Base):
    """
    SQLAlchemy model representing an e-commerce product.
    Contains basic attributes like name, type, subtype, and a relationship to its metadata.
    """
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(100))
    subtype = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    metadata_items = relationship("ProductMetadata", back_populates="product", cascade="all, delete-orphan")

class ProductMetadata(Base):
    """
    SQLAlchemy model representing key-value metadata for a specific product.
    Links back to the Product model via a foreign key.
    """
    __tablename__ = "product_metadata"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    meta_key = Column(String(100), nullable=False)
    meta_value = Column(Text, nullable=False)

    product = relationship("Product", back_populates="metadata_items")

class ChatHistory(Base):
    """
    SQLAlchemy model representing a single chat message in a conversation session.
    Logs the session ID, role (user/agent), raw message content, and timestamp.
    """
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(Enum(RoleEnum), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
