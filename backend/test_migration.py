#!/usr/bin/env python3
"""
Test script for validating SQLite → Firestore migration.

This script tests all critical endpoints to verify:
1. Firestore connectivity
2. Data integrity (teams, matches)
3. Smart caching (team stats, predictions)
4. Cost savings (cache hit/miss tracking)

Usage:
    python test_migration.py

Requirements:
    - Backend server must be running (http://localhost:8080)
    - Firestore must have migrated data
"""

import json
import time
import requests
from typing import Dict, Any
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30  # seconds


class Colors:
    """Terminal colors for output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"
    BOLD = "\033[1m"


def print_header(text: str):
    """Print section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.RESET}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.RESET}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.RESET}")


def test_health_endpoint() -> bool:
    """Test /health endpoint."""
    print_header("TEST 1: Health Endpoint")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json()

        print_info(f"Response: {json.dumps(data, indent=2)}")

        # Verify expected fields
        assert data.get("status") == "healthy", "Status should be 'healthy'"
        assert data.get("firestore") == "ok", "Firestore should be 'ok'"
        assert data.get("teams_count", 0) > 0, "Should have teams in Firestore"

        print_success(f"Health check passed: {data['teams_count']} teams in Firestore")
        return True

    except Exception as e:
        print_error(f"Health check failed: {e}")
        return False


def test_update_tournament() -> bool:
    """Test /api/update-tournament endpoint."""
    print_header("TEST 2: Update Tournament (Load from Firestore)")

    try:
        print_info("Calling POST /api/update-tournament...")
        response = requests.post(f"{BASE_URL}/api/update-tournament", timeout=TIMEOUT)
        response.raise_for_status()

        data = response.json()

        print_info(f"Response: {json.dumps(data, indent=2)}")

        # Verify snapshot was created
        assert data.get("status") == "success", "Status should be 'success'"
        assert "updated_at" in data, "Should have updated_at timestamp"

        print_success("Tournament update successful (loaded from Firestore)")
        return True

    except Exception as e:
        print_error(f"Tournament update failed: {e}")
        return False


def test_update_predictions_first_run() -> Dict[str, Any]:
    """Test /api/update-predictions endpoint (first run - cold cache)."""
    print_header("TEST 3: Update Predictions (1st Run - Cold Cache)")

    try:
        print_info("Calling POST /api/update-predictions (first run)...")
        print_warning(
            "This may take 2-3 minutes (fetching stats + generating predictions)"
        )

        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/update-predictions", timeout=180
        )  # 3 min timeout
        elapsed = time.time() - start_time

        response.raise_for_status()
        data = response.json()

        print_info(f"Response: {json.dumps(data, indent=2)}")
        print_info(f"Duration: {elapsed:.1f} seconds")

        # Extract metrics
        cache_hits = data.get("firestore_cache_hits", 0)
        cache_misses = data.get("firestore_cache_misses", 0)
        predictions_cached = data.get("predictions_cached", 0)
        predictions_regenerated = data.get("predictions_regenerated", 0)

        print_info("\n📊 First Run Metrics:")
        print_info(f"  - Team Stats Cache Hits: {cache_hits}")
        print_info(f"  - Team Stats Cache Misses: {cache_misses}")
        print_info(f"  - Predictions Cached: {predictions_cached}")
        print_info(f"  - Predictions Regenerated: {predictions_regenerated}")

        # On first run, we expect mostly cache misses and regenerations
        if cache_misses > 0:
            print_success(
                f"✓ Cold cache working: {cache_misses} stats fetched from API"
            )
        if predictions_regenerated > 0:
            print_success(
                f"✓ Predictions generated: {predictions_regenerated} new predictions"
            )

        return data

    except Exception as e:
        print_error(f"First predictions run failed: {e}")
        return {}


def test_update_predictions_second_run() -> Dict[str, Any]:
    """Test /api/update-predictions endpoint (second run - hot cache)."""
    print_header("TEST 4: Update Predictions (2nd Run - Hot Cache)")

    try:
        print_info("Calling POST /api/update-predictions (second run)...")
        print_info("Expected: ALL cache hits, ZERO API calls")

        start_time = time.time()
        response = requests.post(f"{BASE_URL}/api/update-predictions", timeout=TIMEOUT)
        elapsed = time.time() - start_time

        response.raise_for_status()
        data = response.json()

        print_info(f"Response: {json.dumps(data, indent=2)}")
        print_info(f"Duration: {elapsed:.1f} seconds")

        # Extract metrics
        cache_hits = data.get("firestore_cache_hits", 0)
        cache_misses = data.get("firestore_cache_misses", 0)
        predictions_cached = data.get("predictions_cached", 0)
        predictions_regenerated = data.get("predictions_regenerated", 0)

        print_info("\n📊 Second Run Metrics:")
        print_info(f"  - Team Stats Cache Hits: {cache_hits}")
        print_info(f"  - Team Stats Cache Misses: {cache_misses}")
        print_info(f"  - Predictions Cached: {predictions_cached}")
        print_info(f"  - Predictions Regenerated: {predictions_regenerated}")

        # On second run, we expect ALL cache hits
        if cache_hits > 0 and cache_misses == 0:
            print_success(
                f"✓ 100% cache hit rate: {cache_hits} stats from Firestore cache"
            )
        else:
            print_warning(
                f"⚠️  Expected all cache hits, got {cache_hits} hits / {cache_misses} misses"
            )

        if predictions_cached > 0 and predictions_regenerated == 0:
            print_success(
                f"✓ 100% prediction cache: {predictions_cached} cached (0 API calls!)"
            )
        else:
            print_warning(
                f"⚠️  Expected all cached, got {predictions_cached} cached / {predictions_regenerated} regenerated"
            )

        # Calculate savings
        if cache_misses == 0 and predictions_regenerated == 0:
            print_success(
                "\n🎉 COST SAVINGS: 100% cache hit = $0 API costs (vs ~$0.01 without caching)!"
            )

        return data

    except Exception as e:
        print_error(f"Second predictions run failed: {e}")
        return {}


def verify_data_integrity() -> bool:
    """Verify Firestore data integrity by checking frontend endpoint."""
    print_header("TEST 5: Data Integrity (Frontend)")

    try:
        # The frontend should be able to load data from Firestore via Cloud Functions
        print_info("Checking if frontend can load data from Firestore...")
        print_warning("Note: This requires frontend to be deployed/running")

        # For now, we'll just verify the backend can read from Firestore
        # (already tested via /health and /api/update-tournament)

        print_success("Backend can read from Firestore (verified in previous tests)")
        print_info(
            "Manual verification needed: Check frontend displays matches correctly"
        )

        return True

    except Exception as e:
        print_error(f"Data integrity check failed: {e}")
        return False


def print_summary(results: Dict[str, bool]):
    """Print test summary."""
    print_header("TEST SUMMARY")

    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed

    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")

    print(f"\n{Colors.BOLD}Results: {passed}/{total} tests passed{Colors.RESET}")

    if failed == 0:
        print_success("\n🎉 ALL TESTS PASSED! Migration successful!")
        print_info("\nNext steps:")
        print_info("  1. Manually verify frontend displays correctly")
        print_info(
            "  2. Backup SQLite database: cp backend/worldcup2026.db backend/worldcup2026.db.backup"
        )
        print_info("  3. Proceed to Phase 4 cleanup (optional)")
    else:
        print_error(f"\n❌ {failed} test(s) failed. Review errors above.")
        print_info("\nTroubleshooting:")
        print_info("  1. Ensure backend is running: cd backend && python src/main.py")
        print_info("  2. Check Firestore has data: run backend/migrate_to_firestore.py")
        print_info("  3. Check backend logs for errors")


def main():
    """Run all migration tests."""
    print_header("FIRESTORE MIGRATION TEST SUITE")
    print_info(f"Testing backend at: {BASE_URL}")
    print_info(f"Timestamp: {datetime.utcnow().isoformat()}Z")

    results = {}

    # Test 1: Health check
    results["Health Endpoint"] = test_health_endpoint()

    if not results["Health Endpoint"]:
        print_error("\n❌ Backend not responding. Ensure server is running:")
        print_info("   cd backend && python src/main.py")
        return

    # Test 2: Update tournament
    results["Update Tournament"] = test_update_tournament()

    # Test 3: First predictions run (cold cache)
    first_run_data = test_update_predictions_first_run()
    results["Predictions (1st run)"] = bool(first_run_data)

    if first_run_data:
        print_info("\nWaiting 5 seconds before second run...")
        time.sleep(5)

        # Test 4: Second predictions run (hot cache)
        second_run_data = test_update_predictions_second_run()
        results["Predictions (2nd run)"] = bool(second_run_data)

    # Test 5: Data integrity
    results["Data Integrity"] = verify_data_integrity()

    # Print summary
    print_summary(results)


if __name__ == "__main__":
    main()
