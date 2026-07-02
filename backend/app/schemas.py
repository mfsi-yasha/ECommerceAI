"""
Pydantic schemas for API request/response validation and serialization.
"""
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductSchema(BaseModel):
    """Represents a product returned by the API, including its key-value metadata."""
    id: int
    name: str
    type: Optional[str] = None
    subtype: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class SearchResponse(BaseModel):
    """Response payload for the /api/search endpoint with the AI response and product list."""
    ai_response: str
    products: List[ProductSchema]


class SearchRequest(BaseModel):
    """Incoming search request body containing the user's query and their session ID."""
    query: str
    session_id: str


class ChatMessage(BaseModel):
    """A single message in the conversation, optionally including products if sent by the agent."""
    role: str
    message: str
    products: Optional[List[ProductSchema]] = None


class ChatHistoryResponse(BaseModel):
    """Response payload for the /api/chat endpoint containing the full conversation history."""
    session_id: str
    history: List[ChatMessage]
