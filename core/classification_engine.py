"""
core/classification_engine.py — ARCH-1: Data classification engine.

Classifies inbound text by sensitivity level using compiled regex patterns.
The result is stored as a plaintext Qdrant payload field so it can be used
as a filter index without decryption (see PLAINTEXT_KEYS in memory_client.py).

Severity order (lowest → highest):
    PUBLIC < INTERNAL < CONFIDENTIAL < PRIVILEGED < PHI < PII < RESTRICTED

Usage:
    from core.classification_engine import classify, Classification

    level = classify("Patient SSN: 123-45-6789")
    # → Classification.PII

    if level >= Classification.PHI:
        # treat as sensitive healthcare data
        ...
"""
import re
from enum import IntEnum


class Classification(IntEnum):
    """Sensitivity levels ordered from lowest (PUBLIC) to highest (RESTRICTED).

    IntEnum gives us free comparison operators (<, >, >=) which are used by
    ARCH-2 (sanitizer) to gate sanitization above a threshold level.
    """
    PUBLIC = 0
    INTERNAL = 1
    CONFIDENTIAL = 2
    PRIVILEGED = 3
    PHI = 4
    PII = 5
    RESTRICTED = 6


# ── Compiled pattern sets, checked highest → lowest ───────────────────────────
# Each entry: (Classification level, list of compiled patterns).
# The first level whose patterns match the input text is returned.
# RESTRICTED is intentionally absent — it cannot be auto-detected via regex.

_RULES: list[tuple[Classification, list[re.Pattern]]] = [

    (Classification.PII, [
        # Social Security Number — with or without dashes/spaces
        re.compile(r'\b\d{3}[-\s]\d{2}[-\s]\d{4}\b'),
        # Credit / debit card — 16 digits in groups of 4
        re.compile(r'\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b'),
        # Email address
        re.compile(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'),
        # US phone number — (555) 123-4567 / 555-123-4567 / +1 555 123 4567
        re.compile(r'\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b'),
    ]),

    (Classification.PHI, [
        # Diagnosis / clinical assessment language
        re.compile(r'\b(diagnos(is|ed with)|patient (has|presents?|is)|'
                   r'chief complaint|assessment|treatment plan|'
                   r'presenting with|clinical (note|history))\b', re.I),
        # Prescription / medication
        re.compile(r'\b(prescri(bed|ption)|medication|dosage|'
                   r'mg (once|twice|daily|per)|drug (name|regimen))\b', re.I),
        # Medical record identifiers
        re.compile(r'\b(mrn|medical record (number|no\.?|#|id)|'
                   r'chart (number|no\.?|id)|patient id)\b', re.I),
        # Date of birth
        re.compile(r'\b(date of birth|d\.?o\.?b\.?|birthdate|born on)\b', re.I),
    ]),

    (Classification.PRIVILEGED, [
        # Attorney-client privilege markers
        re.compile(r'\battorney.client\b', re.I),
        re.compile(r'\b(privileged and confidential|privileged communication)\b', re.I),
        re.compile(r'\b(work product|attorney\'?s? eyes only|legal advice)\b', re.I),
    ]),

    (Classification.CONFIDENTIAL, [
        re.compile(r'\b(confidential|proprietary|trade secret|not for (distribution|release))\b', re.I),
    ]),

    (Classification.INTERNAL, [
        re.compile(r'\b(internal use only|internal only|do not distribute|'
                   r'not for external (use|distribution))\b', re.I),
    ]),
]


def classify(text: str) -> Classification:
    """Return the highest sensitivity Classification level detected in text.

    Checks patterns from highest severity (PII) to lowest (INTERNAL).
    Returns Classification.PUBLIC if no patterns match.
    Classification.RESTRICTED is never auto-assigned — it requires manual tagging.
    """
    for level, patterns in _RULES:
        if any(pattern.search(text) for pattern in patterns):
            return level
    return Classification.PUBLIC
