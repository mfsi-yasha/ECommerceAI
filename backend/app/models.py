"""
SQLAlchemy ORM models for the e-commerce database.
Defines the Products, ProductMetadata, and ChatHistory tables.
"""
import enum

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class RoleEnum(str, enum.Enum):
    """Represents the sender of a chat message: either 'user' or 'agent'."""
    user = "user"
    agent = "agent"


class Product(Base):
    """
    Represents an e-commerce product with a name, category type, and subtype.
    Related metadata is stored separately in the ProductMetadata table.
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
    Stores key-value metadata pairs for a product (e.g. brand, price, color).
    Linked to a parent Product via foreign key.
    """
    __tablename__ = "product_metadata"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    meta_key = Column(String(100), nullable=False)
    meta_value = Column(Text, nullable=False)

    product = relationship("Product", back_populates="metadata_items")


class ChatHistory(Base):
    """
    Logs a single chat message within a conversation session.
    The session_id is a UUID string that groups messages belonging to
    the same conversation. Role indicates whether the sender was the
    user or the AI agent.
    """
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    role = Column(Enum(RoleEnum), nullable=False)
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
