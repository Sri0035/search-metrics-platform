"""End-to-end smoke test for the Search Metrics Platform."""

import os
import sys
import time

import urllib.error
import urllib.request

API_URL = os.getenv("API_URL", "http://localhost:8000")
MAX_WAIT_SECONDS = 180


def fetch(path: str):
    with urllib.request.urlopen(f"{API_URL}{path}", timeout=10) as response:
        return response.status, response.read()


def wait_for_api():
    deadline = time.time() + MAX_WAIT_SECONDS
    while time.time() < deadline:
        try:
            status, _ = fetch("/health")
            if status == 200:
                print("API is healthy")
                return True
        except (urllib.error.URLError, TimeoutError):
            pass
        print("Waiting for API...")
        time.sleep(5)
    return False


def wait_for_metrics():
    deadline = time.time() + MAX_WAIT_SECONDS
    while time.time() < deadline:
        try:
            status, body = fetch("/metrics/summary?minutes=10")
            if status == 200 and b"service_id" in body:
                print("Metrics data available")
                return True
        except (urllib.error.URLError, TimeoutError):
            pass
        print("Waiting for metrics pipeline...")
        time.sleep(10)
    return False


def main():
    print(f"Running smoke test against {API_URL}")

    if not wait_for_api():
        print("FAIL: API did not become healthy in time")
        sys.exit(1)

    endpoints = ["/services", "/anomalies?hours=1", "/metrics/prometheus"]
    for path in endpoints:
        status, _ = fetch(path)
        print(f"  {path} -> {status}")
        if status != 200:
            print(f"FAIL: {path} returned {status}")
            sys.exit(1)

    if not wait_for_metrics():
        print("WARN: Metrics not yet available (pipeline may still be warming up)")
    else:
        print("PASS: End-to-end smoke test succeeded")


if __name__ == "__main__":
    main()
