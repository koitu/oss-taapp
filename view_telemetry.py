#!/usr/bin/env python3
"""View telemetry metrics from the OSPSD service."""

import json
import sys
from pathlib import Path


def format_ms(ms: float) -> str:
    """Format milliseconds with color coding."""
    if ms < 100:
        return f"\033[32m{ms:.2f}ms\033[0m"  # Green for fast
    elif ms < 500:
        return f"\033[33m{ms:.2f}ms\033[0m"  # Yellow for medium
    else:
        return f"\033[31m{ms:.2f}ms\033[0m"  # Red for slow


def format_percentage(pct: float, is_success: bool = True) -> str:
    """Format percentage with color coding."""
    if is_success:
        if pct >= 95:
            return f"\033[32m{pct:.2f}%\033[0m"  # Green for high success
        elif pct >= 80:
            return f"\033[33m{pct:.2f}%\033[0m"  # Yellow for medium success
        else:
            return f"\033[31m{pct:.2f}%\033[0m"  # Red for low success
    else:
        if pct <= 5:
            return f"\033[32m{pct:.2f}%\033[0m"  # Green for low failure
        elif pct <= 20:
            return f"\033[33m{pct:.2f}%\033[0m"  # Yellow for medium failure
        else:
            return f"\033[31m{pct:.2f}%\033[0m"  # Red for high failure


def main():
    """Display telemetry metrics."""
    # Default path or from environment variable
    metrics_path = Path("telemetry/metrics.json")

    if not metrics_path.exists():
        print(f"\n❌ No telemetry data found at {metrics_path}")
        print("\nTo generate telemetry data, run the OSPSD service and interact with it via Discord.")
        print("The service will automatically export metrics to telemetry/metrics.json\n")

        # Show example of what metrics would look like
        print("=" * 70)
        print("📊 EXAMPLE TELEMETRY METRICS")
        print("=" * 70)
        print("\n📈 OVERALL SUMMARY")
        print(f"  Total Events:      42")
        print(f"  Success Rate:      {format_percentage(95.24, is_success=True)}")
        print(f"  Failure Rate:      {format_percentage(4.76, is_success=False)}")
        print(f"  Avg Latency:       {format_ms(234.56)}")

        print("\n⚡ REQUEST LATENCY BY OPERATION")
        print(f"  Chat Message:      {format_ms(1250.30)} (end-to-end)")
        print(f"  AI Generate:       {format_ms(856.42)}")
        print(f"  Ticket Create:     {format_ms(142.18)}")
        print(f"  Ticket List:       {format_ms(89.45)}")
        print(f"  Ticket Get:        {format_ms(67.23)}")
        print(f"  Ticket Update:     {format_ms(134.56)}")
        print(f"  Ticket Delete:     {format_ms(98.12)}")

        print("\n✅ SUCCESS RATE BY OPERATION")
        print(f"  Chat Message:      {format_percentage(98.5, is_success=True)}")
        print(f"  AI Generate:       {format_percentage(96.2, is_success=True)}")
        print(f"  Ticket Create:     {format_percentage(100.0, is_success=True)}")
        print(f"  Ticket List:       {format_percentage(100.0, is_success=True)}")
        print(f"  Ticket Get:        {format_percentage(92.3, is_success=True)}")
        print(f"  Ticket Update:     {format_percentage(100.0, is_success=True)}")
        print(f"  Ticket Delete:     {format_percentage(95.0, is_success=True)}")

        print("\n❌ FAILURE RATE BY OPERATION")
        print(f"  Chat Message:      {format_percentage(1.5, is_success=False)}")
        print(f"  AI Generate:       {format_percentage(3.8, is_success=False)}")
        print(f"  Ticket Create:     {format_percentage(0.0, is_success=False)}")
        print(f"  Ticket List:       {format_percentage(0.0, is_success=False)}")
        print(f"  Ticket Get:        {format_percentage(7.7, is_success=False)}")
        print(f"  Ticket Update:     {format_percentage(0.0, is_success=False)}")
        print(f"  Ticket Delete:     {format_percentage(5.0, is_success=False)}")

        print("\n" + "=" * 70)
        sys.exit(0)

    # Load actual metrics
    with open(metrics_path) as f:
        data = json.load(f)

    summary = data.get("summary", {})
    by_operation = data.get("by_operation", {})

    # Display metrics
    print("\n" + "=" * 70)
    print("📊 OSPSD SERVICE TELEMETRY METRICS")
    print("=" * 70)

    print("\n📈 OVERALL SUMMARY")
    print(f"  Total Events:      {summary.get('total_events', 0)}")
    print(f"  Success Rate:      {format_percentage(summary.get('success_rate', 0), is_success=True)}")
    print(f"  Failure Rate:      {format_percentage(summary.get('failure_rate', 0), is_success=False)}")
    print(f"  Avg Latency:       {format_ms(summary.get('average_latency_ms', 0))}")

    # Request Latency
    print("\n⚡ REQUEST LATENCY BY OPERATION")
    operation_names = {
        "chat_message": "Chat Message",
        "ai_generate": "AI Generate",
        "ticket_create": "Ticket Create",
        "ticket_list": "Ticket List",
        "ticket_get": "Ticket Get",
        "ticket_update": "Ticket Update",
        "ticket_delete": "Ticket Delete",
    }

    for op_key, op_name in operation_names.items():
        if op_key in by_operation:
            latency = by_operation[op_key].get("average_latency_ms", 0)
            events = by_operation[op_key].get("total_events", 0)
            print(f"  {op_name:18} {format_ms(latency):20} ({events} events)")

    # Success Rate
    print("\n✅ SUCCESS RATE BY OPERATION")
    for op_key, op_name in operation_names.items():
        if op_key in by_operation:
            success = by_operation[op_key].get("success_rate", 0)
            print(f"  {op_name:18} {format_percentage(success, is_success=True)}")

    # Failure Rate
    print("\n❌ FAILURE RATE BY OPERATION")
    for op_key, op_name in operation_names.items():
        if op_key in by_operation:
            failure = by_operation[op_key].get("failure_rate", 0)
            print(f"  {op_name:18} {format_percentage(failure, is_success=False)}")

    # Recent Events
    recent_events = data.get("recent_events", [])
    if recent_events:
        print(f"\n📋 RECENT EVENTS (Last {min(5, len(recent_events))})")
        for event in recent_events[-5:]:
            timestamp = event.get("timestamp", "").split("T")[-1][:8]
            operation = event.get("operation", "unknown")
            value = event.get("value", 0)
            success = "✅" if event.get("success") else "❌"
            error = event.get("error_message", "")

            print(f"  {timestamp} {success} {operation:15} {format_ms(value):20}", end="")
            if error:
                print(f" Error: {error[:30]}")
            else:
                print()

    print("\n" + "=" * 70)
    print(f"📁 Metrics file: {metrics_path}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
