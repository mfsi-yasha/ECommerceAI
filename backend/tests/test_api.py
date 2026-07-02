import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, Mock
import uuid

from app.main import app as fastapi_app
from app.database import get_db
from app.models import Base

# Setup in-memory SQLite database
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create the database schema
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db] = override_get_db

client = TestClient(fastapi_app)

def test_health_check():
    """Test that the health check endpoint returns 200 OK."""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_search_with_rag_engine():
    """Test search with a mocked RAG Engine response."""
    test_session_id = str(uuid.uuid4())
    
    # Seed dummy products
    db = TestingSessionLocal()
    from app.models import Product, ProductMetadata
    
    for pid in [1, 5, 8, 12, 16]:
        p = Product(id=pid, name=f"Test Product {pid}", type="shoe", subtype="sneaker")
        db.add(p)
    db.commit()
    db.close()

    # Mock the RAG Engine response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "ai_response": "Here are some great products for you!",
        "product_ids": [1, 5, 8, 12, 16]
    }
    mock_response.raise_for_status = Mock()
    
    with patch("httpx.post", return_value=mock_response):
        response = client.get(f"/api/search?query=running+shoes&session_id={test_session_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["ai_response"] == "Here are some great products for you!"
        assert len(data["products"]) == 5
        assert data["products"][0]["name"] == "Test Product 1"

    # Verify chat history was saved
    response = client.get(f"/api/chat/{test_session_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert data["session_id"] == test_session_id
    assert len(data["history"]) == 2
    
    # Check user message
    assert data["history"][0]["role"] == "user"
    assert data["history"][0]["message"] == "running shoes"
    
    # Check agent message and hydrated products
    assert data["history"][1]["role"] == "agent"
    assert "great products" in data["history"][1]["message"]
    assert len(data["history"][1]["products"]) == 5

def test_search_rag_engine_fallback():
    """Test that search falls back gracefully when RAG Engine is unavailable."""
    test_session_id = str(uuid.uuid4())
    
    with patch("httpx.post", side_effect=Exception("Connection refused")):
        response = client.get(f"/api/search?query=test+query&session_id={test_session_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert "trouble connecting" in data["ai_response"]
        assert isinstance(data["products"], list)

def test_search_endpoint_missing_params():
    """Test validation errors for missing query parameters."""
    response = client.get("/api/search?query=shoes")
    assert response.status_code == 422
    
    response = client.get("/api/search?session_id=123")
    assert response.status_code == 422
