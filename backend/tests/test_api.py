import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
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

def test_search_and_chat_history():
    """Test search interactions and then history retrieval."""
    test_session_id = str(uuid.uuid4())
    
    # 1. Seed dummy products required by the hardcoded placeholder logic
    db = TestingSessionLocal()
    from app.models import Product, ProductMetadata
    
    for pid in [1, 5, 8, 12, 16]:
        p = Product(id=pid, name=f"Test Product {pid}", type="shoe", subtype="sneaker")
        db.add(p)
    db.commit()
    db.close()

    # 2. Hit the search endpoint
    response = client.get(f"/api/search?query=running+shoes&session_id={test_session_id}")
    assert response.status_code == 200
    data = response.json()
    
    assert "ai_response" in data
    assert len(data["products"]) == 5
    assert data["products"][0]["name"] == "Test Product 1"

    # 3. Hit the chat history endpoint to ensure the conversation was saved
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
    assert "placeholder AI response" in data["history"][1]["message"]
    assert len(data["history"][1]["products"]) == 5
    assert data["history"][1]["products"][0]["name"] == "Test Product 1"

def test_search_endpoint_missing_params():
    """Test validation errors for missing query parameters."""
    response = client.get("/api/search?query=shoes")
    assert response.status_code == 422
    
    response = client.get("/api/search?session_id=123")
    assert response.status_code == 422
