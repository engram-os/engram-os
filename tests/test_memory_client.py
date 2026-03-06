"""
Tests for core.memory_client.EncryptedMemoryClient (DSE-1).

Covers:
1. Round-trip: write then search recovers original payload
2. Plaintext filter fields remain visible in raw stored payload
3. Sensitive fields are not present in raw stored payload
4. Legacy compat: points with no "encrypted" field returned as-is
5. Key loading from ENGRAM_ENCRYPTION_KEY env var
6. Key loading auto-generates vault.key when env var is absent
"""
import json
import os
import pytest
from unittest.mock import MagicMock, patch, call
from cryptography.fernet import Fernet


# ─── Helpers ──────────────────────────────────────────────────────────────────

class FakePointStruct:
    """Transparent substitute for qdrant_client.http.models.PointStruct.

    conftest.py stubs the entire qdrant_client.http.models module as a
    MagicMock, so models.PointStruct(...) returns a MagicMock and .payload
    is also a mock — not the real dict.  Patching with this class lets tests
    inspect the actual payload dict that was passed to write().
    """
    def __init__(self, id, vector, payload):
        self.id = id
        self.vector = vector
        self.payload = payload


def make_client(key: bytes | None = None):
    """Return an EncryptedMemoryClient backed by a fresh MagicMock QdrantClient."""
    from core.memory_client import EncryptedMemoryClient
    key = key or Fernet.generate_key()
    mock_qdrant = MagicMock()
    return EncryptedMemoryClient(mock_qdrant, key), mock_qdrant


SAMPLE_PAYLOAD = {
    "memory": "Patient X has diagnosis Y",
    "user_id": "user-abc",
    "matter_id": "case-001",
    "type": "file_ingest",
    "status": "pending",
    "created_at": "2026-03-06T00:00:00",
}


# ─── Test 1: Round-trip ────────────────────────────────────────────────────────

def test_round_trip_write_then_search_recovers_payload():
    """write() encrypts; search() decrypts — caller sees original payload shape."""
    client, mock_qdrant = make_client()

    with patch("core.memory_client.models.PointStruct", FakePointStruct):
        client.write(
            collection_name="second_brain",
            point_id="pt-001",
            vector=[0.1] * 768,
            payload=dict(SAMPLE_PAYLOAD),
        )

    # Capture what was actually stored in Qdrant
    stored_payload = mock_qdrant.upsert.call_args.kwargs["points"][0].payload

    # Simulate Qdrant returning that stored payload on search
    mock_hit = MagicMock()
    mock_hit.id = "pt-001"
    mock_hit.score = 0.9
    mock_hit.payload = dict(stored_payload)

    mock_result = MagicMock()
    mock_result.points = [mock_hit]
    mock_qdrant.query_points.return_value = mock_result

    result = client.search(
        collection_name="second_brain",
        query_vector=[0.1] * 768,
        query_filter=None,
        limit=5,
        score_threshold=0.45,
    )

    recovered = result.points[0].payload
    assert recovered["memory"] == "Patient X has diagnosis Y"
    assert recovered["user_id"] == "user-abc"
    assert recovered["matter_id"] == "case-001"
    assert recovered["type"] == "file_ingest"
    assert recovered["created_at"] == "2026-03-06T00:00:00"


# ─── Test 2: Plaintext filter fields remain visible ───────────────────────────

def test_plaintext_filter_fields_not_encrypted():
    """user_id, matter_id, type, status must be readable in the raw stored payload."""
    client, mock_qdrant = make_client()

    with patch("core.memory_client.models.PointStruct", FakePointStruct):
        client.write(
            collection_name="second_brain",
            point_id="pt-002",
            vector=[0.1] * 768,
            payload=dict(SAMPLE_PAYLOAD),
        )

    stored = mock_qdrant.upsert.call_args.kwargs["points"][0].payload

    assert stored["user_id"] == "user-abc"
    assert stored["matter_id"] == "case-001"
    assert stored["type"] == "file_ingest"
    assert stored["status"] == "pending"


# ─── Test 3: Sensitive fields are not in raw stored payload ───────────────────

def test_sensitive_fields_absent_from_raw_payload():
    """'memory' and 'created_at' must not appear in plaintext in Qdrant."""
    client, mock_qdrant = make_client()

    with patch("core.memory_client.models.PointStruct", FakePointStruct):
        client.write(
            collection_name="second_brain",
            point_id="pt-003",
            vector=[0.1] * 768,
            payload=dict(SAMPLE_PAYLOAD),
        )

    stored = mock_qdrant.upsert.call_args.kwargs["points"][0].payload

    assert "memory" not in stored
    assert "created_at" not in stored
    assert "encrypted" in stored
    # Verify it's not accidentally stored as plain JSON string
    assert "Patient X" not in stored["encrypted"]


# ─── Test 4: Legacy compat — no "encrypted" field ────────────────────────────

def test_legacy_point_without_encrypted_field_returned_as_is():
    """Pre-DSE-1 records with no 'encrypted' field must not crash on search."""
    client, mock_qdrant = make_client()

    legacy_payload = {
        "memory": "old unencrypted memory",
        "user_id": "user-abc",
        "type": "raw_ingestion",
    }

    mock_hit = MagicMock()
    mock_hit.id = "legacy-pt"
    mock_hit.score = 0.8
    mock_hit.payload = dict(legacy_payload)

    mock_result = MagicMock()
    mock_result.points = [mock_hit]
    mock_qdrant.query_points.return_value = mock_result

    result = client.search(
        collection_name="second_brain",
        query_vector=[0.1] * 768,
        query_filter=None,
        limit=5,
        score_threshold=0.45,
    )

    recovered = result.points[0].payload
    assert recovered["memory"] == "old unencrypted memory"
    assert recovered["user_id"] == "user-abc"


# ─── Test 5: Key from env var ─────────────────────────────────────────────────

def test_load_key_uses_env_var_when_set(monkeypatch, tmp_path):
    """load_encryption_key() returns key from ENGRAM_ENCRYPTION_KEY env var."""
    from core.memory_client import load_encryption_key

    expected_key = Fernet.generate_key()
    monkeypatch.setenv("ENGRAM_ENCRYPTION_KEY", expected_key.decode())
    monkeypatch.setattr("core.memory_client.VAULT_PATH", str(tmp_path / "vault.key"))

    key = load_encryption_key()

    assert key == expected_key
    assert not (tmp_path / "vault.key").exists(), "vault.key should not be written when env var is set"


# ─── Test 6: Key auto-generated and persisted to vault.key ───────────────────

def test_load_key_generates_and_persists_vault_key(monkeypatch, tmp_path):
    """Without env var, load_encryption_key() generates a key and saves it."""
    from core.memory_client import load_encryption_key

    vault_path = str(tmp_path / "vault.key")
    monkeypatch.delenv("ENGRAM_ENCRYPTION_KEY", raising=False)
    monkeypatch.setattr("core.memory_client.VAULT_PATH", vault_path)

    key1 = load_encryption_key()

    assert os.path.exists(vault_path)
    assert oct(os.stat(vault_path).st_mode)[-3:] == "600"

    # Second call returns the same key (persistent)
    key2 = load_encryption_key()
    assert key1 == key2


# ─── Test 7: scroll() decrypts payloads when with_payload=True ───────────────

def test_scroll_decrypts_payloads():
    """scroll() with with_payload=True decrypts the encrypted field in results."""
    key = Fernet.generate_key()
    client, mock_qdrant = make_client(key=key)

    # Build a payload that looks like what write() would store
    from cryptography.fernet import Fernet as _Fernet
    f = _Fernet(key)
    secret = {"memory": "scroll memory", "created_at": "2026-03-06"}
    encrypted_val = f.encrypt(json.dumps(secret).encode()).decode()

    stored_payload = {
        "user_id": "user-xyz",
        "matter_id": "case-002",
        "type": "raw_ingestion",
        "encrypted": encrypted_val,
    }

    mock_point = MagicMock()
    mock_point.payload = dict(stored_payload)
    mock_qdrant.scroll.return_value = ([mock_point], None)

    results, _ = client.scroll(
        collection_name="second_brain",
        scroll_filter=None,
        limit=20,
        with_payload=True,
    )

    assert results[0].payload["memory"] == "scroll memory"
    assert "encrypted" not in results[0].payload


# ─── Test 8: scroll() with with_payload=False skips decryption ───────────────

def test_scroll_skips_decryption_when_no_payload():
    """scroll() with with_payload=False passes through without decrypting."""
    client, mock_qdrant = make_client()

    mock_point = MagicMock()
    mock_point.payload = None
    mock_qdrant.scroll.return_value = ([mock_point], None)

    results, _ = client.scroll(
        collection_name="second_brain",
        scroll_filter=None,
        limit=100,
        with_payload=False,
    )

    # Just verifies no exception raised and result is passed through
    assert len(results) == 1
