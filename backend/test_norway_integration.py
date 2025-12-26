#!/usr/bin/env python3
"""
Test script to verify API-Football integration with Norway national team.

This script fetches real match data from API-Football for Norway (team_id=772)
to test the integration before rolling out to all teams.

Usage:
    python test_norway_integration.py
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from data_aggregator import DataAggregator
from db_manager import DBManager
from config import config


def test_norway_fixtures():
    """Test fetching Norway fixtures from API-Football."""

    print("=" * 80)
    print("NORWAY API-FOOTBALL INTEGRATION TEST")
    print("=" * 80)
    print()

    # Check if API key is configured
    if not config.API_FOOTBALL_KEY or config.API_FOOTBALL_KEY == "test-key":
        print("❌ ERROR: API_FOOTBALL_KEY not configured in .env")
        print("   Get your key from: https://www.api-football.com/")
        return False

    print(f"✓ API Key configured: {config.API_FOOTBALL_KEY[:10]}...")
    print()

    # Load Norway from database
    try:
        db_path = os.path.join(os.path.dirname(__file__), "worldcup2026.db")
        db = DBManager(db_path)
        teams = db.load_all_teams()
        norway = next((t for t in teams if t.name == "Norway"), None)

        if not norway:
            print("❌ ERROR: Norway not found in database")
            return False

        if not norway.api_football_id:
            print("❌ ERROR: Norway missing API-Football ID in database")
            print("   Run migration to add API-Football team IDs")
            return False

        print(f"✓ Norway loaded from database")
        print(f"  Internal ID: {norway.id}")
        print(f"  FIFA Code: {norway.fifa_code}")
        print(f"  Group: {norway.group_letter}")
        print(f"  API-Football ID: {norway.api_football_id}")
        print()

    except Exception as e:
        print(f"❌ ERROR loading Norway from database: {e}")
        return False

    # Test 1: Fetch team statistics (last 5 matches)
    print("-" * 80)
    print("TEST 1: Fetching Norway team statistics (last 5 matches)")
    print("-" * 80)
    try:
        aggregator = DataAggregator()
        stats = aggregator.fetch_team_stats(norway.api_football_id)

        print("✅ SUCCESS! Team statistics fetched:")
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

    except Exception as e:
        print(f"❌ ERROR fetching team statistics: {e}")
        print()
        return False

    # Test 2: Fetch past and upcoming fixtures
    print("-" * 80)
    print("TEST 2: Fetching Norway fixtures (last 5 + next 5)")
    print("-" * 80)
    try:
        aggregator = DataAggregator()
        fixtures = aggregator.fetch_team_fixtures(
            norway.api_football_id, last=5, next=5
        )

        print("✅ SUCCESS! Fixtures fetched:")
        print()
        print(
            f"  Total Fixtures: {fixtures['total_count']} "
            f"({len(fixtures['past_fixtures'])} past, {len(fixtures['upcoming_fixtures'])} upcoming)"
        )
        print()

        # Display past fixtures
        if fixtures["past_fixtures"]:
            print("  PAST FIXTURES:")
            for match in fixtures["past_fixtures"]:
                home = match["home_team"]["name"]
                away = match["away_team"]["name"]
                score = f"{match['goals']['home']}-{match['goals']['away']}"
                date = match["date"][:10]
                status = match["status"]
                print(f"    [{status}] {date}: {home} {score} {away}")
            print()

        # Display upcoming fixtures
        if fixtures["upcoming_fixtures"]:
            print("  UPCOMING FIXTURES:")
            for match in fixtures["upcoming_fixtures"]:
                home = match["home_team"]["name"]
                away = match["away_team"]["name"]
                date = match["date"][:10]
                status = match["status"]
                print(f"    [{status}] {date}: {home} vs {away}")
            print()
        else:
            print("  No upcoming fixtures found")
            print()

    except Exception as e:
        print(f"❌ ERROR fetching fixtures: {e}")
        print()
        import traceback

        traceback.print_exc()
        return False

    # Summary
    print("=" * 80)
    print("✅ NORWAY API-FOOTBALL INTEGRATION TEST PASSED!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Add API-Football team IDs for other World Cup 2026 teams")
    print("  2. Update prediction pipeline to use real fixture data")
    print("  3. Test with multiple teams to stay within rate limits")
    print()

    return True


if __name__ == "__main__":
    success = test_norway_fixtures()
    sys.exit(0 if success else 1)
