"""
Multi-User Architecture test suite — MUA-1, MUA-2, MUA-3.

Written before implementation (TDD). Tests will initially fail with
ModuleNotFoundError or ImportError until the following are created/modified:

  - core/user_registry.py       (new)
  - core/matter_registry.py     (new)
  - core/brain.py               (modified — new deps, endpoints, matter logic)
  - agents/tasks.py             (modified — fan_out helpers, user_id params)

Run with: pytest tests/test_multiuser.py -v
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture()
def brain_client():
    from core.brain import app
    return TestClient(app)


@pytest.fixture()
def registry(monkeypatch, tmp_path):
    """Real user_registry module backed by an isolated per-test SQLite DB."""
    import core.user_registry as ur
    monkeypatch.setattr(ur, "DB_PATH", str(tmp_path / "users.db"))
    ur.init_user_db()
    return ur


@pytest.fixture()
def matter_reg(monkeypatch, tmp_path):
    """Real matter_registry module backed by an isolated per-test SQLite DB."""
    import core.matter_registry as mr
    monkeypatch.setattr(mr, "DB_PATH", str(tmp_path / "matters.db"))
    mr.init_matter_db()
    return mr


# ─── MUA-1: User Registry unit tests ─────────────────────────────────────────

class TestUserRegistry:

    def test_bootstrap_creates_admin(self, registry):
        """bootstrap_admin seeds an admin row keyed to LOCAL_USER_ID."""
        registry.bootstrap_admin("admin-001", "supersecret")
        user = registry.get_user_by_key("supersecret")
        assert user is not None
        assert user.id == "admin-001"
        assert user.role == "admin"

    def test_bootstrap_is_idempotent(self, registry):
        """Calling bootstrap_admin twice does not create duplicate rows."""
        registry.bootstrap_admin("admin-001", "key1")
        registry.bootstrap_admin("admin-001", "key1")
        assert len(registry.list_users()) == 1

    def test_bootstrap_empty_key_creates_dev_mode_admin(self, registry):
        """Dev mode: empty raw_api_key still creates exactly one admin row."""
        registry.bootstrap_admin("admin-001", "")
        users = registry.list_users()
        assert len(users) == 1
        assert users[0]["role"] == "admin"

    def test_create_user_key_resolves(self, registry):
        """create_user returns (user_id, raw_key) and the key resolves via lookup."""
        user_id, raw_key = registry.create_user("Alice", role="user")
        assert raw_key  # non-empty
        user = registry.get_user_by_key(raw_key)
        assert user is not None
        assert user.id == user_id
        assert user.display_name == "Alice"
        assert user.role == "user"

    def test_wrong_key_returns_none(self, registry):
        """An unknown key returns None, never raises."""
        registry.create_user("Bob")
        assert registry.get_user_by_key("garbage-key") is None

    def test_list_users_excludes_key_hash(self, registry):
        """list_users never exposes api_key_hash — it must never appear in the response."""
        registry.create_user("Charlie")
        for row in registry.list_users():
            assert "api_key_hash" not in row

    def test_get_user_by_id_found(self, registry):
        uid, _ = registry.create_user("Diana")
        user = registry.get_user_by_id(uid)
        assert user is not None
        assert user.id == uid

    def test_get_user_by_id_missing_returns_none(self, registry):
        assert registry.get_user_by_id("no-such-id") is None


# ─── MUA-1: API auth behaviour ────────────────────────────────────────────────

class TestAuthBehavior:

    def test_dev_mode_chat_no_header_required(self, brain_client):
        """/chat returns 200 without X-API-Key when ENGRAM_API_KEY is '' (dev mode)."""
        fake_vec = [0.1] * 768
        embed_mock = MagicMock()
        embed_mock.json.return_value = {"embedding": fake_vec}
        ollama_mock = MagicMock()
        ollama_mock.json.return_value = {"message": {"content": "ok"}}
        no_match = MagicMock()
        no_match.points = []

        with patch("core.network_gateway.requests.post", side_effect=[embed_mock, ollama_mock]), \
             patch("core.brain.client._qdrant.query_points", return_value=no_match):
            resp = brain_client.post("/chat", json={"text": "hello"})

        assert resp.status_code == 200

    def test_api_me_dev_mode_returns_local_admin(self, brain_client):
        """GET /api/me in dev mode returns the synthetic admin identity."""
        resp = brain_client.get("/api/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "admin"
        # ENGRAM_USER_ID is set to "test-user-uuid-0001" in conftest
        assert data["id"] == "test-user-uuid-0001"

    def test_key_enforced_missing_header_403(self, brain_client):
        """Non-empty ENGRAM_API_KEY + no header → 403."""
        with patch("core.brain._ENGRAM_API_KEY", "enforced-secret"):
            resp = brain_client.post("/chat", json={"text": "hello"})
        assert resp.status_code == 403

    def test_key_enforced_wrong_key_403(self, brain_client):
        """Non-empty ENGRAM_API_KEY + wrong key → 403."""
        with patch("core.brain._ENGRAM_API_KEY", "enforced-secret"), \
             patch("core.brain.get_user_by_key", return_value=None):
            resp = brain_client.post(
                "/chat", json={"text": "hello"},
                headers={"X-API-Key": "wrong-key"}
            )
        assert resp.status_code == 403

    def test_create_user_endpoint_non_admin_403(self, brain_client):
        """POST /api/users with a non-admin key → 403."""
        from core.user_registry import User
        non_admin = User(id="u-001", role="user", display_name="Bob")
        with patch("core.brain._ENGRAM_API_KEY", "enforced-secret"), \
             patch("core.brain.get_user_by_key", return_value=non_admin):
            resp = brain_client.post(
                "/api/users",
                json={"display_name": "Eve", "role": "user"},
                headers={"X-API-Key": "non-admin-key"}
            )
        assert resp.status_code == 403

    def test_list_users_endpoint_non_admin_403(self, brain_client):
        """GET /api/users with a non-admin key → 403."""
        from core.user_registry import User
        non_admin = User(id="u-001", role="user", display_name="Bob")
        with patch("core.brain._ENGRAM_API_KEY", "enforced-secret"), \
             patch("core.brain.get_user_by_key", return_value=non_admin):
            resp = brain_client.get(
                "/api/users",
                headers={"X-API-Key": "non-admin-key"}
            )
        assert resp.status_code == 403


# ─── MUA-2: Matter Registry unit tests ───────────────────────────────────────

class TestMatterRegistry:

    def test_create_matter_returns_id(self, matter_reg):
        mid = matter_reg.create_matter("Case Alpha", created_by="u1")
        assert mid

    def test_creator_has_access(self, matter_reg):
        """Creator is automatically granted access on creation."""
        mid = matter_reg.create_matter("Case Alpha", created_by="u1")
        assert matter_reg.check_access("u1", mid)

    def test_other_user_has_no_access(self, matter_reg):
        mid = matter_reg.create_matter("Case Alpha", created_by="u1")
        assert not matter_reg.check_access("u2", mid)

    def test_grant_access_is_idempotent(self, matter_reg):
        mid = matter_reg.create_matter("Case Alpha", created_by="u1")
        matter_reg.grant_access(mid, "u2", granted_by="u1")
        matter_reg.grant_access(mid, "u2", granted_by="u1")  # second call
        assert matter_reg.check_access("u2", mid)

    def test_list_matters_filtered_to_user(self, matter_reg):
        m1 = matter_reg.create_matter("Mine", created_by="u1")
        m2 = matter_reg.create_matter("Theirs", created_by="u2")
        user_matters = [m["id"] for m in matter_reg.list_matters_for_user("u1")]
        assert m1 in user_matters
        assert m2 not in user_matters

    def test_close_matter_sets_status(self, matter_reg):
        mid = matter_reg.create_matter("Case Beta", created_by="u1")
        matter_reg.close_matter(mid, closed_by="u1")
        m = matter_reg.get_matter(mid)
        assert m["status"] == "closed"
        assert m["closed_at"] is not None

    def test_closed_matter_excluded_from_list(self, matter_reg):
        """list_matters_for_user returns only open matters."""
        mid = matter_reg.create_matter("Case Beta", created_by="u1")
        matter_reg.close_matter(mid, closed_by="u1")
        ids = [m["id"] for m in matter_reg.list_matters_for_user("u1")]
        assert mid not in ids

    def test_get_matter_missing_returns_none(self, matter_reg):
        assert matter_reg.get_matter("ghost-id") is None


# ─── MUA-2: Matter access enforcement (via brain routes) ─────────────────────

class TestMatterEnforcement:

    def test_ingest_without_matter_id_uses_empty_string(self, brain_client):
        """POST /ingest with no matter_id succeeds — legacy data path (matter_id='')."""
        fake_vec = [0.1] * 768
        embed_mock = MagicMock()
        embed_mock.json.return_value = {"embedding": fake_vec}
        no_match = MagicMock()
        no_match.points = []

        with patch("core.network_gateway.requests.post", return_value=embed_mock), \
             patch("core.brain.client._qdrant.query_points", return_value=no_match), \
             patch("core.brain.client._qdrant.upsert"):
            resp = brain_client.post("/ingest", json={"text": "legacy data"})

        assert resp.status_code == 200

    def test_missing_matter_returns_404(self, brain_client):
        """matter_id that doesn't exist in the registry → 404."""
        with patch("core.brain.get_matter", return_value=None):
            resp = brain_client.post(
                "/ingest", json={"text": "ghost matter", "matter_id": "nonexistent"}
            )
        assert resp.status_code == 404

    def test_closed_matter_returns_410(self, brain_client):
        """Accessing a closed matter → 410 Gone."""
        with patch("core.brain.get_matter", return_value={"id": "m1", "status": "closed"}):
            resp = brain_client.post(
                "/ingest", json={"text": "after close", "matter_id": "m1"}
            )
        assert resp.status_code == 410

    def test_non_member_matter_returns_403(self, brain_client):
        """Non-member user providing a matter_id → 403."""
        from core.user_registry import User
        user_b = User(id="u-b", role="user", display_name="Bob")
        with patch("core.brain._ENGRAM_API_KEY", "enforced-secret"), \
             patch("core.brain.get_user_by_key", return_value=user_b), \
             patch("core.brain.get_matter", return_value={"id": "m1", "status": "open"}), \
             patch("core.brain.check_access", return_value=False):
            resp = brain_client.post(
                "/ingest",
                json={"text": "classified doc", "matter_id": "m1"},
                headers={"X-API-Key": "key-b"}
            )
        assert resp.status_code == 403


# ─── MUA-3: Agent fan-out (plain helper functions, Celery-decorator-free) ────

class TestAgentFanOut:

    def test_fan_out_calendar_empty_registry_fires_single_default_task(self):
        """No registered users → one direct call with no args (falls back to LOCAL_USER_ID)."""
        from agents.tasks import _fan_out_calendar
        with patch("agents.tasks.list_users", return_value=[]), \
             patch("agents.tasks.run_calendar_agent") as mock_cal:
            _fan_out_calendar()
        mock_cal.assert_called_once_with()

    def test_fan_out_calendar_fires_per_registered_user(self):
        """Two registered users → two direct calls with distinct user_ids."""
        from agents.tasks import _fan_out_calendar
        users = [{"id": "ua"}, {"id": "ub"}]
        with patch("agents.tasks.list_users", return_value=users), \
             patch("agents.tasks.run_calendar_agent") as mock_cal:
            _fan_out_calendar()
        assert mock_cal.call_count == 2
        called_ids = {c.kwargs["user_id"] for c in mock_cal.call_args_list}
        assert called_ids == {"ua", "ub"}

    def test_fan_out_email_fires_per_registered_user(self):
        """Two registered users → two direct email calls."""
        from agents.tasks import _fan_out_email
        users = [{"id": "ua"}, {"id": "ub"}]
        with patch("agents.tasks.list_users", return_value=users), \
             patch("agents.tasks.run_email_agent") as mock_email:
            _fan_out_email()
        assert mock_email.call_count == 2

    def test_calendar_trigger_route_includes_user_id(self, brain_client):
        """POST /run-agents/calendar fires the agent with the requesting user's ID."""
        with patch("core.brain.run_calendar_agent") as mock_task:
            brain_client.post("/run-agents/calendar")
        mock_task.assert_called_once_with(user_id="test-user-uuid-0001")

    def test_email_trigger_route_includes_user_id(self, brain_client):
        """POST /run-agents/email fires the agent with the requesting user's ID."""
        with patch("core.brain.run_email_agent") as mock_task:
            brain_client.post("/run-agents/email")
        mock_task.assert_called_once_with(user_id="test-user-uuid-0001")
