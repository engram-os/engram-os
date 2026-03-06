"""
core/memory_client.py — DSE-1: Encrypted Qdrant wrapper.

All Qdrant writes go through this module. Sensitive payload fields are
encrypted with Fernet (AES-128-CBC + HMAC-SHA256) before storage. The
fields required for Qdrant filter indexes remain plaintext.

Plaintext fields (never encrypted — required for Qdrant filtering):
    user_id, matter_id, type, classification, status

All other fields (memory, embed_text, created_at, ...) are serialised to
JSON and encrypted into a single "encrypted" field.

Key resolution order:
    1. ENGRAM_ENCRYPTION_KEY env var (base64 Fernet key, 44 chars)
    2. ~/.engram/vault.key (auto-generated on first run, chmod 0o600)
"""
import json
import logging
import os

from cryptography.fernet import Fernet
from qdrant_client import QdrantClient
from qdrant_client.http import models

logger = logging.getLogger(__name__)

# Fields that must remain readable for Qdrant filter indexes.
PLAINTEXT_KEYS: frozenset[str] = frozenset({
    "user_id",
    "matter_id",
    "type",
    "classification",
    "status",
})

VAULT_PATH: str = os.path.expanduser("~/.engram/vault.key")


def load_encryption_key() -> bytes:
    """Return the Fernet key to use for payload encryption.

    Priority:
        1. ENGRAM_ENCRYPTION_KEY env var — base64-encoded Fernet key.
        2. VAULT_PATH file — loaded if it exists.
        3. Auto-generate a new key, persist to VAULT_PATH with mode 0o600.
    """
    env_key = os.getenv("ENGRAM_ENCRYPTION_KEY")
    if env_key:
        return env_key.encode()

    if os.path.exists(VAULT_PATH):
        with open(VAULT_PATH, "rb") as f:
            return f.read().strip()

    # Generate new key and persist it.
    key = Fernet.generate_key()
    os.makedirs(os.path.dirname(VAULT_PATH), exist_ok=True)
    with open(VAULT_PATH, "wb") as f:
        f.write(key)
    os.chmod(VAULT_PATH, 0o600)
    logger.info(f"Generated new encryption key at {VAULT_PATH}")
    return key


class EncryptedMemoryClient:
    """Qdrant client wrapper that transparently encrypts/decrypts payloads.

    Usage:
        key = load_encryption_key()
        qdrant = QdrantClient(host=..., port=6333)
        mem_client = EncryptedMemoryClient(qdrant, key)

        # Write — payload is encrypted before storage
        mem_client.write(collection, point_id, vector, payload)

        # Read — payload is decrypted after retrieval
        result = mem_client.search(collection, query_vector, query_filter, limit, threshold)
    """

    def __init__(self, qdrant_client: QdrantClient, key: bytes) -> None:
        self._qdrant = qdrant_client
        self._fernet = Fernet(key)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _encrypt_payload(self, payload: dict) -> dict:
        """Split payload into plaintext filter fields + one encrypted blob."""
        plaintext = {k: v for k, v in payload.items() if k in PLAINTEXT_KEYS}
        sensitive = {k: v for k, v in payload.items() if k not in PLAINTEXT_KEYS}
        if sensitive:
            ciphertext = self._fernet.encrypt(json.dumps(sensitive).encode()).decode()
            plaintext["encrypted"] = ciphertext
        return plaintext

    def _decrypt_payload(self, payload: dict) -> dict:
        """Decrypt the 'encrypted' field and merge back into payload.

        If 'encrypted' is absent (legacy pre-DSE-1 record), the payload is
        returned unchanged — no crash, no data loss.
        """
        if "encrypted" not in payload:
            return payload  # legacy unencrypted record — pass through
        result = dict(payload)
        ciphertext = result.pop("encrypted").encode()
        sensitive = json.loads(self._fernet.decrypt(ciphertext))
        result.update(sensitive)
        return result

    # ── Public interface ──────────────────────────────────────────────────────

    def write(
        self,
        collection_name: str,
        point_id: str,
        vector: list[float],
        payload: dict,
        classification: str,
    ) -> None:
        """Encrypt payload and upsert a single point.

        classification is stored as a plaintext field (in PLAINTEXT_KEYS) so
        Qdrant can filter on it without decryption. It cannot be omitted —
        every write must declare the sensitivity level of its content.
        """
        stored_payload = self._encrypt_payload({**payload, "classification": classification})
        self._qdrant.upsert(
            collection_name=collection_name,
            points=[models.PointStruct(
                id=point_id,
                vector=vector,
                payload=stored_payload,
            )],
        )

    def search(
        self,
        collection_name: str,
        query_vector: list[float],
        query_filter,
        limit: int,
        score_threshold: float,
    ):
        """Query Qdrant and decrypt payloads in the returned hits."""
        result = self._qdrant.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
        )
        for point in result.points:
            if point.payload:
                point.payload = self._decrypt_payload(point.payload)
        return result

    def scroll(
        self,
        collection_name: str,
        scroll_filter,
        limit: int,
        offset=None,
        with_payload: bool = True,
    ) -> tuple:
        """Scroll Qdrant and decrypt payloads when with_payload=True."""
        kwargs: dict = dict(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            with_payload=with_payload,
        )
        if offset is not None:
            kwargs["offset"] = offset

        points, next_offset = self._qdrant.scroll(**kwargs)

        if with_payload:
            for point in points:
                if point.payload:
                    point.payload = self._decrypt_payload(point.payload)

        return points, next_offset

    def delete(self, collection_name: str, points_selector) -> None:
        """Delete points — no encryption concern, passes through directly."""
        self._qdrant.delete(
            collection_name=collection_name,
            points_selector=points_selector,
        )

    def set_payload(
        self,
        collection_name: str,
        payload: dict,
        points: list,
        wait: bool = True,
    ) -> None:
        """Update plaintext fields (e.g. status) directly — no encryption needed."""
        self._qdrant.set_payload(
            collection_name=collection_name,
            payload=payload,
            points=points,
            wait=wait,
        )
