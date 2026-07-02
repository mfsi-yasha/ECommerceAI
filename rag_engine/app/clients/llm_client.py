import logging
import json
import httpx
from ..config import LLM_BASE_URL, LLM_MODEL

logger = logging.getLogger(__name__)


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


def generate_response(prompt: str, system_prompt: str | None = None, json_mode: bool = False) -> str | None:
    """
    Generate a chat completion via the OpenAI-compatible endpoint.
    Returns the assistant message text, or None on failure (triggers template fallback).
    """
    messages: list[dict] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": LLM_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.1 if json_mode else 0.7,
            "num_predict": 500,
            "num_ctx": 1024
        }
    }
    
    if json_mode:
        payload["format"] = "json"

    try:
        response = httpx.post(
            f"{LLM_BASE_URL}/api/chat",
            json=payload,
            timeout=httpx.Timeout(connect=10.0, read=120.0, write=10.0, pool=10.0),
        )
        response.raise_for_status()
        data = response.json()
        return data["message"]["content"]
    except httpx.ConnectError:
        logger.warning("LLM server not available. Using template fallback.")
        return None
    except httpx.TimeoutException:
        logger.warning("LLM request timed out. Using template fallback.")
        return None
    except Exception as e:
        logger.error(f"LLM generation error: {e}")
        return None
