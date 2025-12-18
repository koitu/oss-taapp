"""Tests for telemetry implementation."""

import json
import sys
import tempfile
from pathlib import Path

import pytest

# Add telemetry modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "telemetry_api" / "src"))

from telemetry_api import MetricType, OperationType
from telemetry_impl import InMemoryTelemetry


def test_record_latency_success() -> None:
    """Test recording successful latency."""
    telemetry = InMemoryTelemetry()

    telemetry.record_latency(OperationType.AI_GENERATE, 150.5, success=True)

    events = telemetry.get_all_events()
    assert len(events) == 1
    assert events[0].operation == OperationType.AI_GENERATE
    assert events[0].metric_type == MetricType.LATENCY
    assert events[0].value == 150.5
    assert events[0].success is True
    assert events[0].error_message is None


def test_record_latency_failure() -> None:
    """Test recording failed latency."""
    telemetry = InMemoryTelemetry()

    telemetry.record_latency(OperationType.TICKET_CREATE, 200.0, success=False, error_message="Connection timeout")

    events = telemetry.get_all_events()
    assert len(events) == 1
    assert events[0].success is False
    assert events[0].error_message == "Connection timeout"


def test_record_success() -> None:
    """Test recording successful operation."""
    telemetry = InMemoryTelemetry()

    telemetry.record_success(OperationType.TICKET_LIST)

    events = telemetry.get_all_events()
    assert len(events) == 1
    assert events[0].metric_type == MetricType.SUCCESS
    assert events[0].success is True


def test_record_failure() -> None:
    """Test recording failed operation."""
    telemetry = InMemoryTelemetry()

    telemetry.record_failure(OperationType.TICKET_DELETE, "Not found")

    events = telemetry.get_all_events()
    assert len(events) == 1
    assert events[0].metric_type == MetricType.FAILURE
    assert events[0].success is False
    assert events[0].error_message == "Not found"


def test_get_success_rate() -> None:
    """Test calculating success rate."""
    telemetry = InMemoryTelemetry()

    # Record 7 successes and 3 failures
    for _ in range(7):
        telemetry.record_success(OperationType.AI_GENERATE)
    for _ in range(3):
        telemetry.record_failure(OperationType.AI_GENERATE, "Error")

    success_rate = telemetry.get_success_rate(OperationType.AI_GENERATE)
    assert success_rate == 70.0


def test_get_failure_rate() -> None:
    """Test calculating failure rate."""
    telemetry = InMemoryTelemetry()

    # Record 8 successes and 2 failures
    for _ in range(8):
        telemetry.record_success(OperationType.TICKET_CREATE)
    for _ in range(2):
        telemetry.record_failure(OperationType.TICKET_CREATE, "Error")

    failure_rate = telemetry.get_failure_rate(OperationType.TICKET_CREATE)
    assert failure_rate == 20.0


def test_get_average_latency() -> None:
    """Test calculating average latency."""
    telemetry = InMemoryTelemetry()

    # Record latencies: 100, 200, 300 ms
    telemetry.record_latency(OperationType.AI_GENERATE, 100.0, success=True)
    telemetry.record_latency(OperationType.AI_GENERATE, 200.0, success=True)
    telemetry.record_latency(OperationType.AI_GENERATE, 300.0, success=True)

    avg_latency = telemetry.get_average_latency(OperationType.AI_GENERATE)
    assert avg_latency == 200.0


def test_get_average_latency_empty() -> None:
    """Test average latency with no events."""
    telemetry = InMemoryTelemetry()

    avg_latency = telemetry.get_average_latency(OperationType.AI_GENERATE)
    assert avg_latency == 0.0


def test_export_metrics() -> None:
    """Test exporting metrics."""
    telemetry = InMemoryTelemetry()

    # Add some test data
    telemetry.record_latency(OperationType.AI_GENERATE, 150.0, success=True)
    telemetry.record_success(OperationType.TICKET_CREATE)
    telemetry.record_failure(OperationType.TICKET_LIST, "Error")

    metrics = telemetry.export_metrics()

    assert "summary" in metrics
    assert "by_operation" in metrics
    assert "recent_events" in metrics

    assert metrics["summary"]["total_events"] == 3
    assert OperationType.AI_GENERATE.value in metrics["by_operation"]


def test_json_export_to_file() -> None:
    """Test exporting metrics to JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / "metrics.json"
        telemetry = InMemoryTelemetry(export_path=str(export_path))

        # Record some events
        telemetry.record_latency(OperationType.AI_GENERATE, 100.0, success=True)
        telemetry.record_success(OperationType.TICKET_CREATE)

        # Verify file was created
        assert export_path.exists()

        # Verify JSON content
        with export_path.open() as f:
            data = json.load(f)

        assert data["summary"]["total_events"] == 2
        assert len(data["recent_events"]) == 2


def test_metadata_tracking() -> None:
    """Test tracking metadata with events."""
    telemetry = InMemoryTelemetry()

    metadata = {"user_id": "123", "channel": "general"}
    telemetry.record_latency(OperationType.CHAT_MESSAGE, 250.0, success=True, metadata=metadata)

    events = telemetry.get_all_events()
    assert events[0].metadata == metadata


def test_multiple_operations() -> None:
    """Test tracking multiple different operations."""
    telemetry = InMemoryTelemetry()

    telemetry.record_latency(OperationType.AI_GENERATE, 100.0, success=True)
    telemetry.record_latency(OperationType.TICKET_CREATE, 50.0, success=True)
    telemetry.record_latency(OperationType.TICKET_LIST, 25.0, success=True)

    # Overall average
    overall_avg = telemetry.get_average_latency()
    assert overall_avg == pytest.approx(58.33, rel=0.01)

    # Per-operation average
    ai_avg = telemetry.get_average_latency(OperationType.AI_GENERATE)
    assert ai_avg == 100.0


def test_success_rate_no_events() -> None:
    """Test success rate with no events returns 0."""
    telemetry = InMemoryTelemetry()

    success_rate = telemetry.get_success_rate(OperationType.AI_GENERATE)
    assert success_rate == 0.0
