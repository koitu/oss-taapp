"""Integration tests for telemetry in realistic scenarios."""

import json
import sys
import tempfile
import time
from pathlib import Path

# Add telemetry modules to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "telemetry_api" / "src"))

from telemetry_api import OperationType
from telemetry_impl import InMemoryTelemetry


def test_end_to_end_workflow() -> None:
    """Test a complete workflow simulating real OSPSD service usage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / "metrics.json"
        telemetry = InMemoryTelemetry(export_path=str(export_path))

        # Simulate a user message workflow
        # 1. AI generates response
        ai_start = time.time()
        time.sleep(0.01)  # Simulate AI processing
        ai_duration = (time.time() - ai_start) * 1000
        telemetry.record_latency(OperationType.AI_GENERATE, ai_duration, success=True)

        # 2. Create a ticket
        ticket_start = time.time()
        time.sleep(0.005)  # Simulate ticket creation
        ticket_duration = (time.time() - ticket_start) * 1000
        telemetry.record_latency(OperationType.TICKET_CREATE, ticket_duration, success=True)

        # 3. List tickets
        list_start = time.time()
        time.sleep(0.003)  # Simulate list operation
        list_duration = (time.time() - list_start) * 1000
        telemetry.record_latency(OperationType.TICKET_LIST, list_duration, success=True)

        # 4. Overall message handling
        total_duration = ai_duration + ticket_duration + list_duration
        telemetry.record_latency(OperationType.CHAT_MESSAGE, total_duration, success=True)

        # Verify metrics
        assert export_path.exists()

        with export_path.open() as f:
            metrics = json.load(f)

        assert metrics["summary"]["total_events"] == 4
        assert metrics["summary"]["success_rate"] == 100.0
        assert metrics["summary"]["failure_rate"] == 0.0

        # Check per-operation metrics
        assert OperationType.AI_GENERATE.value in metrics["by_operation"]
        assert OperationType.TICKET_CREATE.value in metrics["by_operation"]
        assert OperationType.TICKET_LIST.value in metrics["by_operation"]
        assert OperationType.CHAT_MESSAGE.value in metrics["by_operation"]


def test_mixed_success_and_failure() -> None:
    """Test tracking both successful and failed operations."""
    telemetry = InMemoryTelemetry()

    # Successful operations
    telemetry.record_latency(OperationType.AI_GENERATE, 100.0, success=True)
    telemetry.record_latency(OperationType.TICKET_CREATE, 50.0, success=True)
    telemetry.record_latency(OperationType.TICKET_LIST, 30.0, success=True)

    # Failed operations
    telemetry.record_latency(OperationType.AI_GENERATE, 200.0, success=False, error_message="API timeout")
    telemetry.record_failure(OperationType.TICKET_GET, "Ticket not found")

    # Verify overall success rate
    overall_success_rate = telemetry.get_success_rate()
    assert overall_success_rate == 60.0  # 3 successes out of 5 total

    # Verify AI_GENERATE specific metrics
    ai_success_rate = telemetry.get_success_rate(OperationType.AI_GENERATE)
    assert ai_success_rate == 50.0  # 1 success, 1 failure

    # Verify average latency only includes AI_GENERATE latency events
    ai_avg_latency = telemetry.get_average_latency(OperationType.AI_GENERATE)
    assert ai_avg_latency == 150.0  # (100 + 200) / 2


def test_high_volume_operations() -> None:
    """Test telemetry with high volume of operations."""
    telemetry = InMemoryTelemetry()

    # Simulate 100 operations
    for i in range(100):
        operation = OperationType.AI_GENERATE if i % 2 == 0 else OperationType.TICKET_CREATE
        success = i % 10 != 0  # 10% failure rate
        latency = 50.0 + (i % 50)

        if success:
            telemetry.record_latency(operation, latency, success=True)
        else:
            telemetry.record_latency(operation, latency, success=False, error_message=f"Error {i}")

    # Verify total events
    events = telemetry.get_all_events()
    assert len(events) == 100

    # Verify success rate
    success_rate = telemetry.get_success_rate()
    assert success_rate == 90.0

    # Verify export includes only last 100 events
    metrics = telemetry.export_metrics()
    assert len(metrics["recent_events"]) == 100


def test_json_export_structure() -> None:
    """Test that exported JSON has correct structure."""
    with tempfile.TemporaryDirectory() as tmpdir:
        export_path = Path(tmpdir) / "test_metrics.json"
        telemetry = InMemoryTelemetry(export_path=str(export_path))

        # Add varied operations
        telemetry.record_latency(OperationType.AI_GENERATE, 100.0, success=True)
        telemetry.record_latency(OperationType.TICKET_CREATE, 50.0, success=True)
        telemetry.record_failure(OperationType.TICKET_DELETE, "Permission denied")

        with export_path.open() as f:
            data = json.load(f)

        # Verify structure
        assert "summary" in data
        assert "by_operation" in data
        assert "recent_events" in data

        # Verify summary fields
        assert "total_events" in data["summary"]
        assert "success_rate" in data["summary"]
        assert "failure_rate" in data["summary"]
        assert "average_latency_ms" in data["summary"]

        # Verify per-operation fields
        for op_data in data["by_operation"].values():
            assert "success_rate" in op_data
            assert "failure_rate" in op_data
            assert "average_latency_ms" in op_data
            assert "total_events" in op_data

        # Verify recent events fields
        for event in data["recent_events"]:
            assert "timestamp" in event
            assert "operation" in event
            assert "metric_type" in event
            assert "value" in event
            assert "success" in event
