"""
core/sanitizer.py — ARCH-2: PII/PHI sanitization before LLM inference.

Replaces sensitive values in text with typed placeholder tokens before the
content is sent to Ollama. The replacements dict maps each placeholder back
to its original value and is retained locally for the duration of the request
— it is never forwarded to the model.

Threshold: text classified below CONFIDENTIAL is passed through unchanged.
CONFIDENTIAL, PRIVILEGED, PHI, PII, and RESTRICTED all trigger sanitization.

Usage:
    from core.sanitizer import sanitize, SanitizedText
    from core.classification_engine import Classification

    result = sanitize("SSN: 123-45-6789", Classification.PII)
    # result.text         → "SSN: __SSN_0__"
    # result.replacements → {"__SSN_0__": "123-45-6789"}

    # Send result.text to Ollama.
    # result.replacements stays local — never leaves the process.
"""
import re
from collections import namedtuple
from core.classification_engine import Classification


SanitizedText = namedtuple("SanitizedText", ["text", "replacements"])

# Minimum classification level that triggers sanitization.
# PUBLIC and INTERNAL pass through unchanged.
_SANITIZE_THRESHOLD = Classification.CONFIDENTIAL

# ── Redactable patterns — ordered by specificity (most specific first) ────────
# Each entry: (token_label, compiled_pattern).
# Credit card must come before generic 4-digit groups to avoid partial matches.
_REDACT_RULES: list[tuple[str, re.Pattern]] = [
    ("CREDIT_CARD", re.compile(r'\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b')),
    ("SSN",         re.compile(r'\b\d{3}[-\s]\d{2}[-\s]\d{4}\b')),
    ("EMAIL",       re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b')),
    ("PHONE",       re.compile(r'(?<!\w)(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b')),
]


def sanitize(text: str, classification: Classification) -> SanitizedText:
    """Replace sensitive values in text with placeholder tokens.

    Returns a SanitizedText namedtuple containing:
        text         — the sanitized string (safe to send to the LLM)
        replacements — dict mapping each placeholder back to its original value
                       (keep this local; never forward it to the model)

    If classification is below CONFIDENTIAL, returns the original text
    unchanged with an empty replacements dict — zero overhead for public data.
    """
    if classification < _SANITIZE_THRESHOLD:
        return SanitizedText(text=text, replacements={})

    result = text
    replacements: dict[str, str] = {}

    for label, pattern in _REDACT_RULES:
        counter = [0]  # mutable container — closures can't rebind plain ints

        def replacer(match, _label=label, _counter=counter):
            placeholder = f"__{_label}_{_counter[0]}__"
            replacements[placeholder] = match.group(0)
            _counter[0] += 1
            return placeholder

        result = pattern.sub(replacer, result)

    return SanitizedText(text=result, replacements=replacements)
