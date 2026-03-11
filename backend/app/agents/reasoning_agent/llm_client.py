"""
Ollama LLM Client — Wrapper for communicating with local Llama-3.

Handles:
- Connection to Ollama server
- Sending prompts and receiving responses
- Error handling and fallback
- Response parsing
"""
from ollama import Client
from typing import Optional
from app.core.config import get_settings

settings = get_settings()


def _get_client() -> Client:
    """Create an Ollama client with explicit host URL."""
    return Client(host=settings.OLLAMA_BASE_URL)


def call_llm(
    prompt: str,
    system_prompt: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> str:
    """
    Send a prompt to Ollama Llama-3 and return the response text.

    Args:
        prompt: the user/main prompt
        system_prompt: optional system instruction
        temperature: creativity (0.0 = deterministic, 1.0 = creative)
        max_tokens: maximum response length

    Returns:
        LLM response text string

    Raises:
        ConnectionError: if Ollama is not running
    """
    messages = []

    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    messages.append({"role": "user", "content": prompt})

    try:
        client = _get_client()
        response = client.chat(
            model=settings.OLLAMA_MODEL,
            messages=messages,
            options={
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        )
        return response["message"]["content"]

    except Exception as e:
        error_msg = str(e)
        if "connection" in error_msg.lower() or "refused" in error_msg.lower():
            return (
                "[LLM UNAVAILABLE] Ollama is not running. "
                "Please start Ollama with: ollama serve\n"
                "Then pull the model: ollama pull llama3\n\n"
                "Falling back to rule-based explanation."
            )
        else:
            return f"[LLM ERROR] {error_msg}"


def check_ollama_health() -> dict:
    """
    Check if Ollama server is running and model is available.

    Returns:
        Dict with status, model info, or error details.
    """
    try:
        client = _get_client()
        # List available models
        models_response = client.list()

        # Extract model names — handle both dict and object responses
        model_names = []
        models_list = getattr(models_response, "models", None) or models_response.get("models", [])
        for m in models_list:
            if hasattr(m, "model"):
                model_names.append(m.model)
            elif isinstance(m, dict):
                model_names.append(m.get("name", ""))
            else:
                model_names.append(str(m))

        target_model = settings.OLLAMA_MODEL
        model_found = any(target_model in name for name in model_names)

        return {
            "status": "connected",
            "ollama_url": settings.OLLAMA_BASE_URL,
            "target_model": target_model,
            "model_available": model_found,
            "available_models": model_names,
        }

    except Exception as e:
        return {
            "status": "disconnected",
            "ollama_url": settings.OLLAMA_BASE_URL,
            "error": str(e),
            "hint": "Start Ollama with: ollama serve",
        }



