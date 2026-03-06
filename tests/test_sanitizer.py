"""
Tests for core.sanitizer (ARCH-2).

Covers:
1.  SSN replaced with __SSN_0__ and recoverable via replacements dict
2.  Email replaced with __EMAIL_0__
3.  Phone number replaced with __PHONE_0__
4.  Credit card replaced with __CREDIT_CARD_0__
5.  Multiple SSNs get incrementing tokens (__SSN_0__, __SSN_1__)
6.  Mixed PII types all replaced in one pass
7.  Below CONFIDENTIAL threshold → text returned unchanged (PUBLIC)
8.  Below CONFIDENTIAL threshold → text returned unchanged (INTERNAL)
9.  At CONFIDENTIAL threshold → sanitization applied
10. PHI classification → sanitization applied (PHI > CONFIDENTIAL)
11. PII classification → sanitization applied
12. Plain text with no patterns → text unchanged, replacements empty
13. Empty string → SanitizedText("", {}) — no crash
14. Replacement tokens are not themselves present in the sanitized text as raw values
"""
import pytest
from core.sanitizer import sanitize, SanitizedText
from core.classification_engine import Classification


# ─── Test 1–4: Individual pattern replacement ─────────────────────────────────

def test_ssn_replaced_and_recoverable():
    result = sanitize("Patient SSN: 123-45-6789", Classification.PII)
    assert "123-45-6789" not in result.text
    assert "__SSN_0__" in result.text
    assert result.replacements["__SSN_0__"] == "123-45-6789"


def test_email_replaced_and_recoverable():
    result = sanitize("Contact john.doe@hospital.org for records.", Classification.PII)
    assert "john.doe@hospital.org" not in result.text
    assert "__EMAIL_0__" in result.text
    assert result.replacements["__EMAIL_0__"] == "john.doe@hospital.org"


def test_phone_replaced_and_recoverable():
    result = sanitize("Call the patient at (555) 867-5309.", Classification.PHI)
    assert "867-5309" not in result.text
    assert "__PHONE_0__" in result.text
    assert "(555) 867-5309" == result.replacements["__PHONE_0__"]


def test_credit_card_replaced_and_recoverable():
    result = sanitize("Card on file: 4111 1111 1111 1111", Classification.PII)
    assert "4111 1111 1111 1111" not in result.text
    assert "__CREDIT_CARD_0__" in result.text
    assert result.replacements["__CREDIT_CARD_0__"] == "4111 1111 1111 1111"


# ─── Test 5: Multiple instances of the same type ─────────────────────────────

def test_multiple_ssns_get_incrementing_tokens():
    text = "SSN one: 123-45-6789. SSN two: 987-65-4321."
    result = sanitize(text, Classification.PII)
    assert "123-45-6789" not in result.text
    assert "987-65-4321" not in result.text
    assert "__SSN_0__" in result.text
    assert "__SSN_1__" in result.text
    assert result.replacements["__SSN_0__"] == "123-45-6789"
    assert result.replacements["__SSN_1__"] == "987-65-4321"


# ─── Test 6: Mixed types in one pass ─────────────────────────────────────────

def test_mixed_pii_types_all_replaced():
    text = "SSN: 123-45-6789, email: jane@clinic.com, phone: 555-123-4567."
    result = sanitize(text, Classification.PII)
    assert "123-45-6789" not in result.text
    assert "jane@clinic.com" not in result.text
    assert "123-4567" not in result.text
    assert len(result.replacements) == 3


# ─── Test 7–8: Below threshold → passthrough ─────────────────────────────────

def test_public_classification_passes_through_unchanged():
    text = "The quarterly review is scheduled for Thursday."
    result = sanitize(text, Classification.PUBLIC)
    assert result.text == text
    assert result.replacements == {}


def test_internal_classification_passes_through_unchanged():
    text = "Internal use only — budget figures: SSN 123-45-6789"
    result = sanitize(text, Classification.INTERNAL)
    # INTERNAL is below CONFIDENTIAL — no sanitization even if patterns match
    assert result.text == text
    assert result.replacements == {}


# ─── Test 9–11: At and above threshold → sanitized ───────────────────────────

def test_confidential_threshold_triggers_sanitization():
    """CONFIDENTIAL is the minimum level that triggers sanitization."""
    text = "CONFIDENTIAL — contact cfo@company.com for details."
    result = sanitize(text, Classification.CONFIDENTIAL)
    assert "cfo@company.com" not in result.text
    assert "__EMAIL_0__" in result.text


def test_phi_classification_triggers_sanitization():
    text = "Patient DOB 1982-07-19, call (555) 867-5309."
    result = sanitize(text, Classification.PHI)
    assert "867-5309" not in result.text
    assert "__PHONE_0__" in result.text


def test_pii_classification_triggers_sanitization():
    text = "SSN: 123-45-6789 on file."
    result = sanitize(text, Classification.PII)
    assert "123-45-6789" not in result.text


# ─── Test 12–13: Edge cases ───────────────────────────────────────────────────

def test_no_patterns_in_text_returns_unchanged_with_empty_replacements():
    text = "Patient presents with hypertension, well controlled."
    result = sanitize(text, Classification.PHI)
    # PHI classification but no redactable values → text unchanged
    assert result.text == text
    assert result.replacements == {}


def test_empty_string_does_not_crash():
    result = sanitize("", Classification.PII)
    assert result == SanitizedText(text="", replacements={})


# ─── Test 14: Return type is SanitizedText namedtuple ────────────────────────

def test_return_type_is_sanitized_text_namedtuple():
    result = sanitize("hello world", Classification.PUBLIC)
    assert isinstance(result, SanitizedText)
    assert hasattr(result, "text")
    assert hasattr(result, "replacements")
