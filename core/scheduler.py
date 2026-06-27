"""core/scheduler.py — Loads YAML agent definitions and registers them with APScheduler.

Each *.yaml file in DEFINITIONS_DIR describes one agent:

    name: calendar
    description: Scans memories and schedules Google Calendar events
    handler: agents.tasks._fan_out_calendar   # dotted import path
    schedule:
      type: interval      # interval or cron
      minutes: 15
    enabled: true         # omit or set false to disable

Bad handler paths, malformed YAML, or a missing definitions directory are all
logged and skipped — the brain continues to start normally.
"""
import importlib
import logging
import os
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

DEFINITIONS_DIR = Path(os.getenv("AGENT_DEFINITIONS_DIR", "agents/definitions"))


def _resolve_handler(dotted_path: str):
    """Return the callable at `dotted_path`.

    e.g. 'agents.tasks._fan_out_calendar' → the function object.
    Raises ImportError or AttributeError on failure.
    """
    module_path, _, attr = dotted_path.rpartition(".")
    if not module_path:
        raise ImportError(f"Handler path must be 'module.function', got: {dotted_path!r}")
    module = importlib.import_module(module_path)
    return getattr(module, attr)


def load_agent_definitions(scheduler) -> int:
    """Scan DEFINITIONS_DIR for *.yaml files and register each enabled agent.

    Returns the number of successfully registered agents.
    """
    if not DEFINITIONS_DIR.exists():
        logger.warning("Agent definitions directory not found: %s", DEFINITIONS_DIR)
        return 0

    registered = 0
    for path in sorted(DEFINITIONS_DIR.glob("*.yaml")):
        try:
            with open(path) as f:
                spec = yaml.safe_load(f)

            name = spec.get("name", path.stem)

            if not spec.get("enabled", True):
                logger.info("Agent '%s' is disabled — skipping", name)
                continue

            handler = _resolve_handler(spec["handler"])
            schedule = spec.get("schedule", {})
            schedule_type = schedule.get("type", "interval")
            schedule_kwargs = {k: v for k, v in schedule.items() if k != "type"}

            scheduler.add_job(
                handler,
                schedule_type,
                max_instances=1,
                misfire_grace_time=60,
                **schedule_kwargs,
            )
            logger.info("Registered agent '%s' (%s: %s)", name, schedule_type, schedule_kwargs)
            registered += 1

        except Exception as e:
            logger.error("Failed to load agent definition '%s': %s", path.name, e)

    return registered
