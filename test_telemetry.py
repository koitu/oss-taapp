"""Test script to verify telemetry is working on all services."""

import httpx
import time

def test_service_telemetry(service_name: str, base_url: str, test_endpoint: str):
    """Test telemetry for a service.
    
    Args:
        service_name: Name of the service being tested
        base_url: Base URL of the service
        test_endpoint: Endpoint to test (e.g., "/health")
    """
    print(f"\n{'='*60}")
    print(f"Testing {service_name}")
    print(f"{'='*60}")
    
    try:
        # Make a test request
        print(f"Making request to {base_url}{test_endpoint}...")
        response = httpx.get(f"{base_url}{test_endpoint}", timeout=10.0)
        print(f"✓ Response status: {response.status_code}")
        print(f"✓ Response body: {response.json()}")
        
        # Wait a moment for metrics to be recorded
        time.sleep(0.5)
        
        # Check metrics endpoint
        print(f"\nFetching metrics from {base_url}/metrics...")
        metrics_response = httpx.get(f"{base_url}/metrics", timeout=10.0)
        print(f"✓ Metrics endpoint status: {metrics_response.status_code}")
        
        # Parse and display relevant metrics
        metrics_text = metrics_response.text
        print("\n📊 Key Metrics:")
        print("-" * 60)
        
        for line in metrics_text.split('\n'):
            if line.startswith('#'):
                continue
            if any(keyword in line for keyword in ['http_requests_total', 'http_request_duration_seconds', 'http_request_errors_total']):
                print(f"  {line}")
        
        print(f"\n✅ {service_name} telemetry is working!")
        return True
        
    except Exception as e:
        print(f"\n❌ Error testing {service_name}: {e}")
        return False


def main():
    """Test telemetry on all services."""
    print("\n" + "="*60)
    print("TELEMETRY VERIFICATION TEST")
    print("="*60)
    print("\nThis script tests that Prometheus metrics are being")
    print("collected and exposed on all services.")
    print("\nNOTE: Services must be running for this test to work.")
    print("="*60)
    
    services = [
        ("Discord Service", "http://localhost:8001", "/health"),
        ("OpenAI Service", "http://localhost:8002", "/health"),
        ("Mail Service", "http://localhost:8000", "/health"),
    ]
    
    results = {}
    for service_name, base_url, endpoint in services:
        results[service_name] = test_service_telemetry(service_name, base_url, endpoint)
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for service_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {service_name}")
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All services have telemetry working!")
    else:
        print("\n⚠️  Some services failed. Make sure they are running.")
        print("\nTo start services:")
        print("  Discord: uv run python run_discord_service.py")
        print("  OpenAI:  uv run uvicorn openai_client_service.main:app --port 8002")
        print("  Mail:    uv run python run_service.py")


if __name__ == "__main__":
    main()

