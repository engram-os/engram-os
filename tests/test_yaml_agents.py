"""tests/test_yaml_agents.py — Tests for the YAML agent definition loader."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml


def _write(tmp_path: Path, name: str, spec: dict) -> Path:
    p = tmp_path / f"{name}.yaml"
    p.write_text(yaml.dump(spec))
    return p


def _scheduler():
    return MagicMock()


def _valid_spec(**overrides) -> dict:
    base = {
        "name": "test-agent",
        "description": "Test agent",
        "handler": "logging.getLogger",   # always importable + callable
        "schedule": {"type": "interval", "minutes": 15},
        "enabled": True,
    }
    base.update(overrides)
    return base


# ── core behaviour ────────────────────────────────────────────────────────────

def test_registers_enabled_agent(tmp_path):
    """A single enabled YAML file → add_job called once with the interval kwargs."""
    _write(tmp_path, "myagent", _valid_spec())
    sched = _scheduler()

    with patch("core.scheduler.DEFINITIONS_DIR", tmp_path):
        from core.scheduler import load_agent_definitions
        count = load_agent_definitions(sched)

    assert count == 1
    sched.add_job.assert_called_once()
    kwargs = sched.add_job.call_args.kwargs
    assert kwargs["minutes"] == 15
    assert kwargs["max_instances"] == 1


def test_skips_disabled_agent(tmp_path):
    """enabled: false → job not registered, count stays 0."""
    _write(tmp_path, "disabled", _valid_spec(enabled=False))
    sched = _scheduler()

    with patch("core.scheduler.DEFINITIONS_DIR", tmp_path):
        from core.scheduler import load_agent_definitions
        count = load_agent_definitions(sched)

    assert count == 0
    sched.add_job.assert_not_called()


def test_skips_invalid_handler(tmp_path):
    """An unresolvable handler path logs the error and skips — no exception raised."""
    _write(tmp_path, "bad", _valid_spec(handler="no.such.module.fn"))
    sched = _scheduler()

    with patch("core.scheduler.DEFINITIONS_DIR", tmp_path):
        from core.scheduler import load_agent_definitions
        count = load_agent_definitions(sched)   # must not raise

    assert count == 0
    sched.add_job.assert_not_called()


def test_missing_definitions_dir_returns_zero(tmp_path):
    """A non-existent definitions directory returns 0 without crashing."""
    sched = _scheduler()
    missing = tmp_path / "nonexistent"

    with patch("core.scheduler.DEFINITIONS_DIR", missing):
        from core.scheduler import load_agent_definitions
        count = load_agent_definitions(sched)

    assert count == 0
    sched.add_job.assert_not_called()


def test_multiple_agents_all_registered(tmp_path):
    """Two valid YAML files → add_job called twice, count is 2."""
    _write(tmp_path, "agent_a", _valid_spec(name="a", schedule={"type": "interval", "minutes": 10}))
    _write(tmp_path, "agent_b", _valid_spec(name="b", schedule={"type": "interval", "hours": 2}))
    sched = _scheduler()

    with patch("core.scheduler.DEFINITIONS_DIR", tmp_path):
        from core.scheduler import load_agent_definitions
        count = load_agent_definitions(sched)

    assert count == 2
    assert sched.add_job.call_count == 2


def test_cron_schedule_registered(tmp_path):
    """Cron-type schedule passes hour/minute kwargs to add_job."""
    _write(tmp_path, "daily", _valid_spec(schedule={"type": "cron", "hour": 8, "minute": 0}))
    sched = _scheduler()

    with patch("core.scheduler.DEFINITIONS_DIR", tmp_path):
        from core.scheduler import load_agent_definitions
        count = load_agent_definitions(sched)

    assert count == 1
    kwargs = sched.add_job.call_args.kwargs
    assert kwargs["hour"] == 8
    assert kwargs["minute"] == 0
    # schedule type is the positional arg (index 1)
    assert sched.add_job.call_args.args[1] == "cron"
