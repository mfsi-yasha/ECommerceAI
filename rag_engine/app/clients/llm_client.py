import logging
import httpx
from functools import lru_cache
from langchain_core.language_models.chat_models import BaseChatModel

from ..config import (
    LLM_BASE_URL, 
    LLM_MODEL, 
    GROQ_API_KEY, 
    GROQ_MODEL, 
    LOCAL_MODEL_LABEL, 
    CLOUD_MODEL_LABEL
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=2)
def get_llm(provider: str) -> BaseChatModel:
    """
    Factory function: returns the appropriate LangChain ChatModel.

    Args:
        provider: The requested LLM provider label.

    Returns:
        A LangChain ChatModel instance ready for tool binding.
    """
    # Fallback if an empty provider is somehow passed
    if not provider:
        provider = LOCAL_MODEL_LABEL

    if CLOUD_MODEL_LABEL in provider or "groq" in provider.lower():
        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY not set. Falling back to local Ollama.")
            return _get_ollama_llm()
        return _get_groq_llm()
    else:
        return _get_ollama_llm()


def _get_groq_llm() -> BaseChatModel:
    """Return a ChatGroq instance pointed at the free Groq cloud API."""
    from langchain_groq import ChatGroq

    logger.info(f"Using Groq cloud LLM: {GROQ_MODEL}")
    return ChatGroq(
        model=GROQ_MODEL,
        api_key=GROQ_API_KEY,
        temperature=0.3,
        max_tokens=1024,
    )


def _get_ollama_llm() -> BaseChatModel:
    """Return a ChatOllama instance pointed at the local Ollama server."""
    from langchain_ollama import ChatOllama

    logger.info(f"Using local Ollama LLM: {LLM_MODEL} at {LLM_BASE_URL}")
    return ChatOllama(
        model=LLM_MODEL,
        base_url=LLM_BASE_URL,
        temperature=0.3,
        num_predict=500,
        num_ctx=1024,
    )




def pull_model(model: str | None = None) -> bool:
    """
    Pull (download) the LLM model on the Ollama server.
    Only needed on first run — subsequent starts use the cached model.
    Setting stream=false makes Ollama return a single response when done.
    """
    model = model or LLM_MODEL
    try:
        logger.info(f"Pulling LLM model '{model}'... (this may take several minutes on first run)")
        response = httpx.post(
            f"{LLM_BASE_URL}/api/pull",
            json={"name": model, "stream": False},
            timeout=httpx.Timeout(connect=10.0, read=600.0, write=10.0, pool=10.0),
        )
        response.raise_for_status()
        logger.info(f"Model '{model}' is ready.")
        return True
    except httpx.ConnectError:
        logger.warning(f"LLM server not reachable at {LLM_BASE_URL}. Model pull skipped.")
        return False
    except httpx.TimeoutException:
        logger.warning(f"Model pull timed out for '{model}'. It may still be downloading.")
        return False
    except Exception as e:
        logger.warning(f"Could not pull model '{model}': {e}")
        return False


def check_model_available() -> bool:
    """Check whether the configured model is already loaded on Ollama."""
    try:
        response = httpx.get(f"{LLM_BASE_URL}/api/tags", timeout=5.0)
        response.raise_for_status()
        models = response.json().get("models", [])
        return any(m.get("name", "").startswith(LLM_MODEL) for m in models)
    except Exception:
        return False
