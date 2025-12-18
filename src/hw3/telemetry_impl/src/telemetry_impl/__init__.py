"""In-memory telemetry implementation with JSON export."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from telemetry_api import (
    MetricType,
    OperationType,
    TelemetryEvent,
    TelemetryInterface,
)


class InMemoryTelemetry(TelemetryInterface):
    """In-memory telemetry collector with file export capabilities."""

    def __init__(self, export_path: str | None = None) -> None:
        """Initialize the telemetry collector.

        Args:
            export_path: Optional path to export metrics to JSON file

        """
        self.events: list[TelemetryEvent] = []
        self.export_path = export_path

    def record_latency(
        self,
        operation: OperationType,
        duration_ms: float,
        *,
        success: bool = True,
        error_message: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Record latency for an operation."""
        event = TelemetryEvent(
            timestamp=datetime.now(tz=UTC),
            operation=operation,
            metric_type=MetricType.LATENCY,
            value=duration_ms,
            success=success,
            error_message=error_message,
            metadata=metadata,
        )
        self.events.append(event)

        # Auto-export if path is set
        if self.export_path:
            self._write_to_file()

    def record_success(
        self,
        operation: OperationType,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Record a successful operation."""
        event = TelemetryEvent(
            timestamp=datetime.now(tz=UTC),
            operation=operation,
            metric_type=MetricType.SUCCESS,
            value=1.0,
            success=True,
            metadata=metadata,
        )
        self.events.append(event)

        if self.export_path:
            self._write_to_file()

    def record_failure(
        self,
        operation: OperationType,
        error_message: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Record a failed operation."""
        event = TelemetryEvent(
            timestamp=datetime.now(tz=UTC),
            operation=operation,
            metric_type=MetricType.FAILURE,
            value=1.0,
            success=False,
            error_message=error_message,
            metadata=metadata,
        )
        self.events.append(event)

        if self.export_path:
            self._write_to_file()

    def get_success_rate(self, operation: OperationType | None = None) -> float:
        """Get success rate for operations."""
        events = [e for e in self.events if e.operation == operation] if operation else self.events

        if not events:
            return 0.0

        total = len(events)
        successes = sum(1 for e in events if e.success)
        return (successes / total) * 100

    def get_failure_rate(self, operation: OperationType | None = None) -> float:
        """Get failure rate for operations."""
        return 100.0 - self.get_success_rate(operation)

    def get_average_latency(self, operation: OperationType | None = None) -> float:
        """Get average latency for operations."""
        if operation:
            latency_events = [e for e in self.events if e.operation == operation and e.metric_type == MetricType.LATENCY]
        else:
            latency_events = [e for e in self.events if e.metric_type == MetricType.LATENCY]

        if not latency_events:
            return 0.0

        return sum(e.value for e in latency_events) / len(latency_events)

    def get_all_events(self) -> list[TelemetryEvent]:
        """Get all recorded telemetry events."""
        return self.events.copy()

    def export_metrics(self) -> dict[str, Any]:
        """Export all metrics in a structured format."""
        metrics: dict[str, Any] = {
            "summary": {
                "total_events": len(self.events),
                "success_rate": self.get_success_rate(),
                "failure_rate": self.get_failure_rate(),
                "average_latency_ms": self.get_average_latency(),
            },
            "by_operation": {},
        }

        # Calculate per-operation metrics
        operations = {e.operation for e in self.events}
        for op in operations:
            metrics["by_operation"][op.value] = {
                "success_rate": self.get_success_rate(op),
                "failure_rate": self.get_failure_rate(op),
                "average_latency_ms": self.get_average_latency(op),
                "total_events": len([e for e in self.events if e.operation == op]),
            }

        # Add recent events (last 100)
        metrics["recent_events"] = [
            {
                "timestamp": e.timestamp.isoformat(),
                "operation": e.operation.value,
                "metric_type": e.metric_type.value,
                "value": e.value,
                "success": e.success,
                "error_message": e.error_message,
                "metadata": e.metadata,
            }
            for e in self.events[-100:]
        ]

        return metrics

    def _write_to_file(self) -> None:
        """Write metrics to JSON file."""
        if not self.export_path:
            return

        metrics = self.export_metrics()
        path = Path(self.export_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as f:
            json.dump(metrics, f, indent=2)
