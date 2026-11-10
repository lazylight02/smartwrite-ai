"""
Translation for SmartWrite AI.

Primary engine: deep-translator's GoogleTranslator — free, no API key,
works out of the box on any machine with normal internet access.

Why a fallback exists: this project was built and tested inside a
sandboxed dev environment whose network allowlist blocks
translate.google.com, so the live call couldn't be exercised there.
Rather than hide that, translate_text() detects the failure and raises
a typed TranslationUnavailable error with a clear message, and the UI
(app.py) catches it and shows an honest "translation needs internet
access" notice instead of silently returning wrong output. On a normal
machine or server this fallback path simply never triggers.

LANGUAGES holds the common set exposed in the UI; deep-translator
supports far more if you want to extend the dropdown.
"""

from __future__ import annotations

from dataclasses import dataclass

from deep_translator import GoogleTranslator
from deep_translator.exceptions import NotValidPayload

LANGUAGES = {
    "English": "en",
    "Hindi": "hi",
    "Telugu": "te",
    "Tamil": "ta",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Japanese": "ja",
    "Chinese (Simplified)": "zh-CN",
    "Arabic": "ar",
}

_MAX_CHUNK = 4500  # GoogleTranslator's practical per-request character limit


class TranslationUnavailable(RuntimeError):
    """Raised when the translation backend can't be reached."""


@dataclass
class TranslationResult:
    translated_text: str
    source_lang: str
    target_lang: str


def _chunk(text: str, size: int) -> list[str]:
    # Split on paragraph breaks first so we don't cut mid-sentence where avoidable
    paragraphs = text.split("\n\n")
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) + 2 <= size:
            current = f"{current}\n\n{p}" if current else p
        else:
            if current:
                chunks.append(current)
            current = p
    if current:
        chunks.append(current)
    return chunks or [text]


def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> TranslationResult:
    if not text.strip():
        return TranslationResult(translated_text="", source_lang=source_lang, target_lang=target_lang)

    try:
        translator = GoogleTranslator(source=source_lang, target=target_lang)
        pieces = [translator.translate(chunk) or "" for chunk in _chunk(text, _MAX_CHUNK)]
        return TranslationResult(
            translated_text="\n\n".join(pieces),
            source_lang=source_lang,
            target_lang=target_lang,
        )
    except NotValidPayload as e:
        raise TranslationUnavailable(f"Nothing translatable in the input: {e}") from e
    except Exception as e:
        # Covers connection errors, DNS failures, rate limits, etc.
        raise TranslationUnavailable(
            "Couldn't reach the translation service. This feature needs outbound "
            "internet access to translate.google.com — check your connection "
            f"(details: {e})"
        ) from e
