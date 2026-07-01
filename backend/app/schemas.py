from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional

class ProductSchema(BaseModel):
    """
    Pydantic schema representing the structure of a product returned by the API.
    Used for serialization and type validation.
    """
    id: int
    name: str
    type: Optional[str] = None
    subtype: Optional[str] = None
    metadata: Dict[str, str] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)

class SearchResponse(BaseModel):
    """
    Pydantic schema for the response payload of the /api/search endpoint.
    Includes the AI's textual response and a list of hydrated product objects.
    """
    ai_response: str
    products: List[ProductSchema]

class SearchRequest(BaseModel):
    """
    Pydantic schema for the incoming search request body (if used in a POST endpoint).
    """
    query: str
    session_id: str

class ChatMessage(BaseModel):
    """
    Pydantic schema representing a single formatted chat message in the chat history.
    Optionally contains a list of hydrated products if the sender was the agent.
    """
    role: str
    message: str
    products: Optional[List[ProductSchema]] = None

class ChatHistoryResponse(BaseModel):
    """
    Pydantic schema for the response payload of the /api/chat endpoint.
    Contains the session ID and the full reconstructed conversation history.
    """
    session_id: str
    history: List[ChatMessage]
