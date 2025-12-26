#!/usr/bin/env python3
"""
Quick test script to verify API-Football integration.

Usage:
    python test_api_football.py

Requires:
    - .env file with API_FOOTBALL_KEY
    - requests library installed
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_aggregator import DataAggregator
from config import config


def test_api_football():
    """Test API-Football integration with a single team."""

    print("=" * 60)
    print("API-FOOTBALL INTEGRATION TEST")
    print("=" * 60)

    # Check if API key is configured
    if not config.API_FOOTBALL_KEY or config.API_FOOTBALL_KEY == "test-key":
        print("❌ ERROR: API_FOOTBALL_KEY not configured in .env")
        print("   Get your key from: https://www.api-football.com/")
        return False

    print(f"✓ API Key configured: {config.API_FOOTBALL_KEY[:10]}...")
    print()

    # Test with a well-known team (e.g., Manchester United = 33)
    team_id = 33  # Manchester United
    team_name = "Manchester United"

    print(f"Fetching stats for {team_name} (team_id={team_id})...")
    print("-" * 60)

    try:
        aggregator = DataAggregator()
        stats = aggregator.fetch_team_stats(team_id)

        print("✅ SUCCESS! API-Football returned data:")
        print()
        print(f"  Form String:       {stats['form_string']}")
        print(f"  Clean Sheets:      {stats['clean_sheets']}")
        print(f"  Average xG:        {stats['avg_xg']}")
        print(f"  Data Completeness: {stats['data_completeness']:.1%}")
        print(f"  Confidence:        {stats['confidence']}")
        print(f"  Fallback Mode:     {stats['fallback_mode']}")
        print()

        if stats["avg_xg"] is None:
            print("ℹ️  Note: xG data not available (expected for free tier)")
            print("   Predictions will use rule-based fallback")

        print()
        print("=" * 60)
        print("✅ API-FOOTBALL INTEGRATION WORKING!")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ ERROR: {e}")
        print()
        print("Common issues:")
        print("  - Invalid API key")
        print("  - Rate limit exceeded (100 requests/day on free tier)")
        print("  - Network connection issues")
        print("  - Team ID not found")
        print()
        return False


if __name__ == "__main__":
    success = test_api_football()
    sys.exit(0 if success else 1)
