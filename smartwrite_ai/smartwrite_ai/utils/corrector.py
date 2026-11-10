"""
Text correction for SmartWrite AI.

Uses pyspellchecker — a pure-Python, fully offline spell checker built
on word-frequency lists (no network, no API key). It's edit-distance
based rather than context-aware, so it catches typos reliably but won't
fix real-word grammar errors ("their" vs "there"). That trade-off is
intentional: it means this feature works identically whether you're
offline, on a flaky hostel wifi, or behind a college firewall.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from spellchecker import SpellChecker

_spell = SpellChecker()
_WORD_RE = re.compile(r"[A-Za-z']+")


@dataclass
class Correction:
    original: str
    suggestion: str
    position: tuple[int, int]  # char offsets in the original text


@dataclass
class CorrectionResult:
    corrected_text: str
    corrections: list[Correction] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.corrections)


def correct_text(text: str) -> CorrectionResult:
    corrections: list[Correction] = []
    out_chars = list(text)
    offset = 0  # tracks length drift as we splice in replacements

    for match in _WORD_RE.finditer(text):
        word = match.group()
        lower = word.lower()

        if lower in _spell:
            continue
        if not _spell.unknown([lower]):
            continue

        fix = _spell.correction(lower)
        if not fix or fix == lower:
            continue

        # Preserve original capitalisation style
        if word.isupper():
            fix = fix.upper()
        elif word[0].isupper():
            fix = fix.capitalize()

        start, end = match.start() + offset, match.end() + offset
        out_chars[start:end] = list(fix)
        offset += len(fix) - len(word)

        corrections.append(Correction(original=word, suggestion=fix, position=(match.start(), match.end())))

    return CorrectionResult(corrected_text="".join(out_chars), corrections=corrections)
