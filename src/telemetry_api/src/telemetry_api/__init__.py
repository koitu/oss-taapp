"""Abstract telemetry API for observability and monitoring."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class MetricType(StrEnum):
    """Types of metrics that can be recorded."""

    LATENCY = "latency"
    SUCCESS = "success"
    FAILURE = "failure"
    COUNTER = "counter"


class OperationType(StrEnum):
    """Types of operations that can be monitored."""

    CHAT_MESSAGE = "chat_message"
    AI_GENERATE = "ai_generate"
    TICKET_CREATE = "ticket_create"
    TICKET_LIST = "ticket_list"
    TICKET_GET = "ticket_get"
    TICKET_UPDATE = "ticket_update"
    TICKET_DELETE = "ticket_delete"


@dataclass
class TelemetryEvent:
    """Represents a single telemetry event."""

    timestamp: datetime
    operation: OperationType
    metric_type: MetricType
    value: float
    success: bool
    error_message: str | None = None
    metadata: dict[str, str] | None = None


class TelemetryInterface(ABC):
    """Abstract interface for telemetry collection and reporting."""

    @abstractmethod
    def record_latency(
        self,
        operation: OperationType,
        duration_ms: float,
        success: bool = True,
        error_message: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Record latency for an operation.

        Args:
            operation: The type of operation being measured
            duration_ms: Duration in milliseconds
            success: Whether the operation succeeded
            error_message: Error message if the operation failed
            metadata: Additional context about the operation

        """
        raise NotImplementedError

    @abstractmethod
    def record_success(
        self,
        operation: OperationType,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Record a successful operation.

        Args:
            operation: The type of operation
            metadata: Additional context about the operation

        """
        raise NotImplementedError

    @abstractmethod
    def record_failure(
        self,
        operation: OperationType,
        error_message: str,
        metadata: dict[str, str] | None = None,
    ) -> None:
        """Record a failed operation.

        Args:
            operation: The type of operation
            error_message: Description of the failure
            metadata: Additional context about the operation

        """
        raise NotImplementedError

    @abstractmethod
    def get_success_rate(self, operation: OperationType | None = None) -> float:
        """Get success rate for operations.

        Args:
            operation: Specific operation type, or None for overall rate

        Returns:
            Success rate as a percentage (0-100)

        """
        raise NotImplementedError

    @abstractmethod
    def get_failure_rate(self, operation: OperationType | None = None) -> float:
        """Get failure rate for operations.

        Args:
            operation: Specific operation type, or None for overall rate

        Returns:
            Failure rate as a percentage (0-100)

        """
        raise NotImplementedError

    @abstractmethod
    def get_average_latency(self, operation: OperationType | None = None) -> float:
        """Get average latency for operations.

        Args:
            operation: Specific operation type, or None for overall average

        Returns:
            Average latency in milliseconds

        """
        raise NotImplementedError

    @abstractmethod
    def get_all_events(self) -> list[TelemetryEvent]:
        """Get all recorded telemetry events.

        Returns:
            List of all telemetry events

        """
        raise NotImplementedError

    @abstractmethod
    def export_metrics(self) -> dict[str, any]:
        """Export all metrics in a structured format.

        Returns:
            Dictionary containing all metrics and statistics

        """
        raise NotImplementedError
