"""Test message model."""

from datetime import datetime, timezone

from masstransit.models.message import Message


def test_sent_time_is_timezone_aware_utc():
    """We expect sentTime to be UTC with an explicit offset."""
    # system under test
    message = Message()

    # assertions
    sent_time = datetime.fromisoformat(message.sentTime)
    assert sent_time.utcoffset() == timezone.utc.utcoffset(None)


def test_lag_is_time_elapsed_since_sent():
    """We expect lag to be the positive elapsed time, not raise on an aware sentTime."""
    # assertions
    assert 0 <= Message().lag.total_seconds() < 5


def test_lag_handles_naive_sent_time():
    """We expect legacy naive sentTime (no offset) to be treated as UTC, not raise."""
    # system under test
    message = Message(sentTime="2024-01-01T12:00:00.000000")

    # assertions
    assert message.lag.total_seconds() > 0
