"""Tests for Phase 3 architectural quality changes.

Covers:
- Audit log TTL pruning (_maybe_prune, verify_audit_chain with pruned boundary)
- git_automator _extract_commit_msg (DEAD-2 replacement)
"""
import os
import sqlite3
import tempfile

import pytest


# ─── Audit log TTL ────────────────────────────────────────────────────────────

@pytest.fixture
def patched_logger(tmp_path, monkeypatch):
    """Set up agents.logger pointing at a temp DB with no socket path."""
    monkeypatch.setenv("AUDIT_HMAC_SECRET", "test-secret-for-unit-tests")
    monkeypatch.setenv("AUDIT_SOCKET_PATH", "")
    db_path = str(tmp_path / "test_audit.db")
    import agents.logger as lg
    monkeypatch.setattr(lg, "DB_PATH", db_path)
    monkeypatch.setattr(lg, "AUDIT_SOCKET_PATH", "")
    monkeypatch.setattr(lg, "_AUDIT_SECRET", b"test-secret-for-unit-tests")
    lg.init_db()
    return lg


def _insert_n_rows(lg, n: int) -> None:
    """Insert n minimal audit rows directly via log_agent_action."""
    for i in range(n):
        lg.log_agent_action("TestAgent", "TEST", f"row {i}")


class TestAuditLogTTL:

    def test_prevent_delete_trigger_removed(self, patched_logger):
        """The prevent_delete trigger must no longer exist in the schema."""
        conn = sqlite3.connect(patched_logger.DB_PATH)
        triggers = {row[1] for row in conn.execute(
            "SELECT type, name FROM sqlite_master WHERE type='trigger'"
        ).fetchall()}
        conn.close()
        assert "prevent_delete" not in triggers

    def test_prevent_update_trigger_still_present(self, patched_logger):
        """The prevent_update trigger must still block in-place edits.

        SQLite RAISE(ABORT) raises IntegrityError (not OperationalError).
        """
        lg = patched_logger
        lg.log_agent_action("A", "B", "c")
        conn = sqlite3.connect(lg.DB_PATH)
        with pytest.raises(sqlite3.IntegrityError, match="append-only"):
            conn.execute("UPDATE activity_log SET details = 'tampered' WHERE id = 1")
        conn.close()

    def test_maybe_prune_does_not_fire_below_threshold(self, patched_logger):
        """Prune should not delete rows when count is well below 50K."""
        lg = patched_logger
        _insert_n_rows(lg, 10)
        conn = sqlite3.connect(lg.DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]
        conn.close()
        assert count == 10

    def test_maybe_prune_fires_on_interval(self, patched_logger, monkeypatch):
        """When count exceeds _PRUNE_MAX_ROWS, excess rows are deleted."""
        lg = patched_logger
        # Lower the thresholds to something testable without inserting 50K rows.
        monkeypatch.setattr(lg, "_PRUNE_INTERVAL", 5)
        monkeypatch.setattr(lg, "_PRUNE_MAX_ROWS", 8)

        # Insert 10 rows — prune fires on the 10th (10 % 5 == 0) and should
        # trim back to 8 rows.
        _insert_n_rows(lg, 10)

        conn = sqlite3.connect(lg.DB_PATH)
        count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]
        conn.close()
        assert count == 8

    def test_verify_chain_valid_for_full_log(self, patched_logger):
        """Chain verification must pass for a clean unmodified log."""
        lg = patched_logger
        _insert_n_rows(lg, 5)
        result = lg.verify_audit_chain()
        assert result["valid"] is True
        assert result["entries_checked"] == 5
        assert "pruned" not in result

    def test_verify_chain_valid_after_prune(self, patched_logger, monkeypatch):
        """Chain verification must pass for a pruned log and set pruned=True."""
        lg = patched_logger
        monkeypatch.setattr(lg, "_PRUNE_INTERVAL", 5)
        monkeypatch.setattr(lg, "_PRUNE_MAX_ROWS", 8)

        _insert_n_rows(lg, 10)  # prune fires, trimming oldest rows

        result = lg.verify_audit_chain()
        assert result["valid"] is True
        assert result.get("pruned") is True
        assert result["entries_checked"] == 8


# ─── _extract_commit_msg (DEAD-2) ────────────────────────────────────────────

@pytest.fixture
def extract_fn():
    """Load the real agents.git_automator, bypassing the conftest stub.

    conftest.py installs a MagicMock for agents.git_automator so the brain app
    can mount an empty router without triggering Google API calls. We temporarily
    remove that stub so we can import and test the real module.
    """
    import importlib
    import sys
    stub = sys.modules.pop("agents.git_automator", None)
    try:
        real_mod = importlib.import_module("agents.git_automator")
        fn = real_mod._extract_commit_msg
    finally:
        if stub is not None:
            sys.modules["agents.git_automator"] = stub
    return fn


class TestExtractCommitMsg:

    def test_clean_conventional_commit_returned_as_is(self, extract_fn):
        assert extract_fn("feat: add dark mode toggle") == "feat: add dark mode toggle"

    def test_strips_preamble_phrase(self, extract_fn):
        raw = "Here is the commit message:\nfeat: add dark mode toggle"
        assert extract_fn(raw) == "feat: add dark mode toggle"

    def test_strips_markdown_code_fence(self, extract_fn):
        raw = "```\nfix: correct null pointer in payment flow\n```"
        assert extract_fn(raw) == "fix: correct null pointer in payment flow"

    def test_strips_wrapping_backticks(self, extract_fn):
        raw = "`chore: update dependencies`"
        assert extract_fn(raw) == "chore: update dependencies"

    def test_falls_back_to_first_nonempty_line(self, extract_fn):
        """When no conventional type found, return first non-empty line."""
        raw = "Update the README file"
        assert extract_fn(raw) == "Update the README file"

    def test_handles_scoped_commit(self, extract_fn):
        raw = "feat(auth): add OAuth2 PKCE flow"
        assert extract_fn(raw) == "feat(auth): add OAuth2 PKCE flow"

    def test_handles_breaking_change_marker(self, extract_fn):
        raw = "feat!: drop Python 3.9 support"
        assert extract_fn(raw) == "feat!: drop Python 3.9 support"

    def test_prose_before_conventional_line_is_stripped(self, extract_fn):
        raw = (
            "I've analyzed the diff. Here's a suitable commit message:\n\n"
            "refactor: extract payment logic into dedicated service\n\n"
            "Let me know if you'd like changes."
        )
        assert extract_fn(raw) == "refactor: extract payment logic into dedicated service"
