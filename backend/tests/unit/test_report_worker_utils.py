from datetime import datetime, timezone

from app.workers.report_exports import _clean_status, _parse_datetime


def test_parse_datetime_from_iso_string() -> None:
    value = _parse_datetime("2026-01-01T10:00:00Z")
    assert value == datetime(2026, 1, 1, 10, 0, 0, tzinfo=timezone.utc)


def test_parse_datetime_empty_string_is_none() -> None:
    assert _parse_datetime("   ") is None


def test_clean_status_none_or_blank_is_none() -> None:
    assert _clean_status(None) is None
    assert _clean_status("  ") is None


def test_clean_status_normalizes_text() -> None:
    assert _clean_status(" paid ") == "paid"
