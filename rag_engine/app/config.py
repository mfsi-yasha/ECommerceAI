import os

POSTGRES_USER = os.getenv("POSTGRES_USER", "ecommerce_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "ecommerce_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "ecommerce_db")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "products")

LLM_HOST = os.getenv("LLM_HOST", "localhost")
LLM_PORT = os.getenv("LLM_PORT", "11434")
LLM_MODEL = os.getenv("LLM_MODEL", "phi3")
LLM_BASE_URL = f"http://{LLM_HOST}:{LLM_PORT}"

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIM = 384  # Dimension for all-MiniLM-L6-v2

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
LOCAL_MODEL_LABEL = os.getenv("LOCAL_MODEL_LABEL", "Local (Llama 3.2)")
CLOUD_MODEL_LABEL = os.getenv("CLOUD_MODEL_LABEL", "Cloud (Groq Llama 3.1)")
