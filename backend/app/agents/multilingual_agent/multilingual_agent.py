"""
Multilingual Agent — Language detection and translation using Llama-3.

Handles:
- Detecting input language
- Translating non-English input to English for processing
- Translating English responses back to the user's language
"""
from app.agents.reasoning_agent.llm_client import call_llm
from app.core.constants import LANG_ENGLISH, SUPPORTED_LANGUAGES


def detect_language(text: str) -> str:
    """
    Detect the language of the input text using LLM.

    Returns one of the SUPPORTED_LANGUAGES or 'English' as default.
    """
    prompt = (
        f"Identify the language of the following text. "
        f"Reply with ONLY the language name — one of: {', '.join(SUPPORTED_LANGUAGES)}.\n\n"
        f"Text: \"{text}\"\n\n"
        f"Language:"
    )
    try:
        response = call_llm(prompt, temperature=0.0, max_tokens=20)
        detected = response.strip().strip(".")
        # Match to supported languages
        for lang in SUPPORTED_LANGUAGES:
            if lang.lower() in detected.lower():
                return lang
        return LANG_ENGLISH
    except Exception:
        return LANG_ENGLISH


def translate_to_english(text: str, source_language: str) -> str:
    """Translate text from source_language to English using LLM."""
    if source_language == LANG_ENGLISH:
        return text

    prompt = (
        f"Translate the following {source_language} text to English.\n"
        f"Provide ONLY the English translation, nothing else.\n\n"
        f"{source_language} Text: \"{text}\"\n\n"
        f"English Translation:"
    )
    try:
        return call_llm(prompt, temperature=0.1, max_tokens=512).strip()
    except Exception:
        return text


def translate_from_english(text: str, target_language: str) -> str:
    """Translate English text to target_language using LLM."""
    if target_language == LANG_ENGLISH:
        return text

    prompt = (
        f"You are a professional banking translator.\n"
        f"Translate the following English text to {target_language}.\n"
        f"Maintain a professional, empathetic banking tone.\n"
        f"Provide ONLY the {target_language} translation, nothing else.\n\n"
        f"English Text:\n{text}\n\n"
        f"{target_language} Translation:"
    )
    try:
        return call_llm(prompt, temperature=0.1, max_tokens=1024).strip()
    except Exception:
        return text