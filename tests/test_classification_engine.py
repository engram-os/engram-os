"""
Tests for core.classification_engine (ARCH-1).

Covers:
1.  SSN detected as PII
2.  Credit card number detected as PII
3.  Email address detected as PII
4.  Phone number detected as PII
5.  Diagnosis language detected as PHI
6.  MRN / medical record language detected as PHI
7.  Date of birth language detected as PHI
8.  Medication / prescription language detected as PHI
9.  Attorney-client language detected as PRIVILEGED
10. "Confidential" language detected as CONFIDENTIAL
11. "Internal use only" detected as INTERNAL
12. Plain text defaults to PUBLIC
13. Highest severity wins when multiple patterns match (SSN in a medical context → PII not PHI)
14. Classification enum is ordered correctly (PUBLIC is lowest, RESTRICTED is highest)
"""
import pytest
from core.classification_engine import classify, Classification


# ─── Test 1-4: PII patterns ───────────────────────────────────────────────────

def test_ssn_classified_as_pii():
    assert classify("Patient SSN: 123-45-6789") == Classification.PII

def test_ssn_no_dashes_classified_as_pii():
    assert classify("Social security number is 123 45 6789") == Classification.PII

def test_credit_card_classified_as_pii():
    assert classify("Card number: 4111 1111 1111 1111") == Classification.PII

def test_email_address_classified_as_pii():
    assert classify("Please contact john.doe@hospital.org for details.") == Classification.PII

def test_phone_number_classified_as_pii():
    assert classify("Call the patient at (555) 867-5309.") == Classification.PII

def test_phone_number_dashes_classified_as_pii():
    assert classify("Emergency contact: 555-867-5309") == Classification.PII


# ─── Test 5-8: PHI patterns ───────────────────────────────────────────────────

def test_diagnosis_language_classified_as_phi():
    assert classify("Patient is diagnosed with Type 2 diabetes.") == Classification.PHI

def test_patient_presents_classified_as_phi():
    assert classify("Patient presents with shortness of breath and chest pain.") == Classification.PHI

def test_medical_record_number_classified_as_phi():
    assert classify("MRN: 00482910 — admitted 2026-01-14") == Classification.PHI

def test_date_of_birth_classified_as_phi():
    assert classify("Date of birth: 1982-07-19") == Classification.PHI

def test_prescription_classified_as_phi():
    assert classify("Prescribed lisinopril 10mg once daily.") == Classification.PHI

def test_assessment_section_classified_as_phi():
    assert classify("Assessment: hypertension, well-controlled on current regimen.") == Classification.PHI


# ─── Test 9: PRIVILEGED ───────────────────────────────────────────────────────

def test_attorney_client_classified_as_privileged():
    assert classify("This communication is protected by attorney-client privilege.") == Classification.PRIVILEGED

def test_work_product_classified_as_privileged():
    assert classify("This document constitutes attorney work product.") == Classification.PRIVILEGED


# ─── Test 10: CONFIDENTIAL ────────────────────────────────────────────────────

def test_confidential_language_classified_as_confidential():
    assert classify("CONFIDENTIAL: Do not forward this document.") == Classification.CONFIDENTIAL

def test_proprietary_classified_as_confidential():
    assert classify("This is proprietary information belonging to Arrow Health.") == Classification.CONFIDENTIAL


# ─── Test 11: INTERNAL ────────────────────────────────────────────────────────

def test_internal_use_only_classified_as_internal():
    assert classify("INTERNAL USE ONLY — not for external distribution.") == Classification.INTERNAL


# ─── Test 12: PUBLIC default ──────────────────────────────────────────────────

def test_plain_text_classified_as_public():
    assert classify("The project meeting is scheduled for next Thursday.") == Classification.PUBLIC

def test_empty_string_classified_as_public():
    assert classify("") == Classification.PUBLIC


# ─── Test 13: Highest severity wins ──────────────────────────────────────────

def test_ssn_in_medical_context_returns_pii_not_phi():
    """When both PHI and PII patterns match, PII (higher) must win."""
    text = "Patient diagnosed with hypertension. SSN: 123-45-6789."
    result = classify(text)
    assert result == Classification.PII
    assert result != Classification.PHI

def test_confidential_medical_note_returns_phi_not_confidential():
    """PHI > CONFIDENTIAL — medical content beats a generic confidential marker."""
    text = "CONFIDENTIAL — Patient presents with acute chest pain."
    result = classify(text)
    assert result == Classification.PHI
    assert result != Classification.CONFIDENTIAL


# ─── Test 14: Enum ordering ───────────────────────────────────────────────────

def test_classification_enum_ordering():
    """PUBLIC is the lowest; RESTRICTED is the highest."""
    ordered = [
        Classification.PUBLIC,
        Classification.INTERNAL,
        Classification.CONFIDENTIAL,
        Classification.PRIVILEGED,
        Classification.PHI,
        Classification.PII,
        Classification.RESTRICTED,
    ]
    # Each level should have a strictly higher value than the one before it
    for i in range(len(ordered) - 1):
        assert ordered[i] < ordered[i + 1], (
            f"{ordered[i]} should be less than {ordered[i + 1]}"
        )
