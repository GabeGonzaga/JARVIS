from __future__ import annotations

import json
from typing import Any, Dict, Optional

from jarvis.llm.ollama import chat

SUPPORTED_LANGUAGES = {
    "en": "English",
    "pt": "Portuguese (Portugal)",
    "es": "Spanish",
    "fr": "French",
}

DEFAULT_LANGUAGE = "pt"


def _detect_language_preference(text: str) -> Optional[str]:
    """Detect if user is requesting a language change."""
    text_lower = text.lower().strip()
    
    # English triggers
    if any(phrase in text_lower for phrase in [
        "speak in english", "change to english", "english please", 
        "switch to english", "fala em inglês", "falar em inglês"
    ]):
        return "en"
    
    # Portuguese triggers
    if any(phrase in text_lower for phrase in [
        "fala em português", "falar em português", "speak in portuguese",
        "change to portuguese", "português por favor", "portuguese please"
    ]):
        return "pt"
    
    # Spanish triggers
    if any(phrase in text_lower for phrase in [
        "habla en español", "hablar en español", "speak in spanish",
        "change to spanish", "español por favor", "spanish please",
        "fala em espanhol", "falar em espanhol"
    ]):
        return "es"
    
    # French triggers
    if any(phrase in text_lower for phrase in [
        "parle en français", "parler en français", "speak in french",
        "change to french", "français s'il vous plaît", "french please",
        "fala em francês", "falar em francês"
    ]):
        return "fr"
    
    return None


def translate_text(text: str, target_lang: str, model: str = "gemma2:2b") -> str:
    """
    Translate text to target language using Ollama.
    Falls back to original text if translation fails.
    """
    if not text or not text.strip():
        return text
    
    if target_lang not in SUPPORTED_LANGUAGES:
        return text
    
    # Skip translation if target is Portuguese (default JARVIS language)
    if target_lang == "pt":
        return text
    
    target_name = SUPPORTED_LANGUAGES[target_lang]
    
    system_prompt = f"""You are a translator. Translate the following text to {target_name}.
Rules:
- Maintain the same tone and formality
- Keep technical terms and names unchanged
- Preserve markdown and formatting
- Return ONLY the translated text, no explanations
- Keep "Sir" as "Sir" in all languages (it's a proper form of address)"""

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ]
        
        translated = chat(model, messages).strip()
        
        # Basic validation: if translation seems wrong, return original
        if not translated or len(translated) < len(text) * 0.3:
            return text
        
        return translated
    except Exception:
        # If translation fails, return original text
        return text


def get_language_name(lang_code: str) -> str:
    """Get human-readable language name."""
    return SUPPORTED_LANGUAGES.get(lang_code, "Portuguese (Portugal)")


def format_language_change_response(new_lang: str) -> str:
    """Format response when language is changed."""
    responses = {
        "en": "Sir, I will now speak in English.",
        "pt": "Sir, vou agora falar em Português.",
        "es": "Sir, ahora hablaré en Español.",
        "fr": "Sir, je parlerai maintenant en Français.",
    }
    return responses.get(new_lang, responses["pt"])
