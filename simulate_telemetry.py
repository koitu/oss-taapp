#!/usr/bin/env python3
"""Simulate telemetry data to demonstrate the metrics system."""

import sys
import time
from pathlib import Path

# Add telemetry modules to path
sys.path.insert(0, str(Path(__file__).parent / "src" / "telemetry_api" / "src"))
sys.path.insert(0, str(Path(__file__).parent / "src" / "telemetry_impl" / "src"))

from telemetry_api import OperationType  # noqa: E402
from telemetry_impl import InMemoryTelemetry  # noqa: E402


def simulate_workflow():
    """Simulate realistic OSPSD service usage."""
    print("🚀 Simulating OSPSD service telemetry...\n")

    telemetry = InMemoryTelemetry(export_path="telemetry/metrics.json")

    scenarios = [
        ("User asks to create a ticket", True, 100, 150, 80),
        ("User lists tickets", True, 90, None, 70),
        ("User requests ticket details", True, 85, None, 60),
        ("AI timeout occurs", False, 2500, None, None),
        ("User creates another ticket", True, 95, 140, 75),
        ("User updates ticket status", True, 88, None, None),
        ("Ticket not found error", True, 92, None, None),
        ("User deletes ticket", True, 87, None, None),
        ("User lists all tickets", True, 93, None, 85),
        ("Successful chat interaction", True, 105, 145, None),
    ]

    for i, (description, success, ai_latency, create_latency, list_latency) in enumerate(scenarios, 1):
        print(f"[{i}/10] {description}")

        # Simulate AI generation
        if success and ai_latency < 1000:
            telemetry.record_latency(OperationType.AI_GENERATE, ai_latency, success=True)
        elif not success:
            telemetry.record_latency(
                OperationType.AI_GENERATE,
                ai_latency,
                success=False,
                error_message="API timeout"
            )
            telemetry.record_failure(OperationType.AI_GENERATE, "API timeout")
            continue
        else:
            telemetry.record_latency(OperationType.AI_GENERATE, ai_latency, success=True)

        # Simulate ticket operations
        if create_latency:
            telemetry.record_latency(OperationType.TICKET_CREATE, create_latency, success=True)
        elif list_latency:
            telemetry.record_latency(OperationType.TICKET_LIST, list_latency, success=True)
        elif "details" in description:
            if "not found" in description:
                telemetry.record_latency(OperationType.TICKET_GET, 65, success=True)
            else:
                telemetry.record_latency(OperationType.TICKET_GET, 60, success=True)
        elif "updates" in description:
            telemetry.record_latency(OperationType.TICKET_UPDATE, 130, success=True)
        elif "deletes" in description:
            telemetry.record_latency(OperationType.TICKET_DELETE, 95, success=True)

        # Overall message latency
        total_latency = ai_latency + (create_latency or list_latency or 60)
        telemetry.record_latency(OperationType.CHAT_MESSAGE, total_latency, success=True)

        time.sleep(0.1)

    print("\n✅ Simulation complete!")
    print(f"📊 Metrics exported to telemetry/metrics.json\n")
    print("Run: python3 view_telemetry.py")


if __name__ == "__main__":
    simulate_workflow()
