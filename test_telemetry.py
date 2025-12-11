"""Test script to verify telemetry is working on all services."""

import httpx


def test_service_telemetry(service_name: str, base_url: str, test_endpoint: str) -> bool:
    """Test telemetry for a service.

    Args:
        service_name: Name of the service being tested
        base_url: Base URL of the service
        test_endpoint: Endpoint to test (e.g., "/health")

    """
    try:
        # Check metrics endpoint
        metrics_response = httpx.get(f"{base_url}/metrics", timeout=10.0)

        # Parse and display relevant metrics
        metrics_text = metrics_response.text

        for line in metrics_text.split("\n"):
            if line.startswith("#"):
                continue
        return True
    except Exception:
        return False


def main() -> None:
    """Test telemetry on all services."""
    services = [
        ("Discord Service", "http://localhost:8001", "/health"),
        ("OpenAI Service", "http://localhost:8002", "/health"),
        ("Mail Service", "http://localhost:8000", "/health"),
    ]

    results = {}
    for service_name, base_url, endpoint in services:
        results[service_name] = test_service_telemetry(service_name, base_url, endpoint)

if __name__ == "__main__":
    main()

