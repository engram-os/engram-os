"""
tests/test_tools.py — agents/tools.py: calendar event time detection tests.

Covers the has_time_component check in add_calendar_event():
  - Midnight (00:00) must produce a timed dateTime event, not an all-day event
  - A date-only string (no time) must produce an all-day date event
  - An explicit non-midnight time must produce a timed dateTime event

Run with: pytest tests/ -v
"""
import datetime
import pytest
from unittest.mock import patch, MagicMock

from agents.tools import add_calendar_event

_FUTURE = datetime.datetime(2030, 1, 15)  # safely in the future — avoids +7d shift


def _make_service():
    """Returns (mock_service, mock_insert) so tests can inspect the event body."""
    mock_insert = MagicMock(
        return_value=MagicMock(execute=MagicMock(return_value={"htmlLink": "http://x"}))
    )
    mock_service = MagicMock()
    mock_service.events.return_value.insert = mock_insert
    return mock_service, mock_insert


def test_midnight_creates_timed_event():
    """Parsed midnight (00:00) → dateTime event, not all-day."""
    service, mock_insert = _make_service()
    midnight = _FUTURE.replace(hour=0, minute=0)

    with patch("agents.tools.get_calendar_service", return_value=service), \
         patch("agents.tools.dateutil_parser.parse", return_value=midnight):
        add_calendar_event("Midnight standup", "midnight Wednesday")

    body = mock_insert.call_args.kwargs["body"]
    assert "dateTime" in body["start"], (
        "midnight should produce a timed (dateTime) event, not all-day"
    )


def test_date_only_string_creates_all_day_event():
    """Parse returning sentinel values (22:47) → all-day date event."""
    service, mock_insert = _make_service()
    # Sentinel: what dateutil returns when no time is present in the string
    no_time_result = _FUTURE.replace(hour=22, minute=47)

    with patch("agents.tools.get_calendar_service", return_value=service), \
         patch("agents.tools.dateutil_parser.parse", return_value=no_time_result):
        add_calendar_event("All-day block", "next Thursday")

    body = mock_insert.call_args.kwargs["body"]
    assert "date" in body["start"] and "dateTime" not in body["start"], (
        "no time in string → should produce all-day (date) event"
    )


def test_explicit_time_creates_timed_event():
    """Any non-sentinel parsed time → dateTime event."""
    service, mock_insert = _make_service()
    two_pm = _FUTURE.replace(hour=14, minute=0)

    with patch("agents.tools.get_calendar_service", return_value=service), \
         patch("agents.tools.dateutil_parser.parse", return_value=two_pm):
        add_calendar_event("Afternoon sync", "Thursday at 2pm")

    body = mock_insert.call_args.kwargs["body"]
    assert "dateTime" in body["start"], "2pm should produce a timed (dateTime) event"
