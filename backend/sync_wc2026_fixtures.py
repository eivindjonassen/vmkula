"""
Sync World Cup 2026 fixtures from API-Football to Firestore.

This script:
1. Fetches all WC 2026 fixtures from API-Football
2. Maps them to existing matches in Firestore by teams
3. Updates Firestore with real fixture IDs, dates, and venues
4. Validates the mapping

Usage:
    python sync_wc2026_fixtures.py
"""

import logging
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Any

import requests

from src.config import config
from src.firestore_manager import FirestoreManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def fetch_wc2026_fixtures() -> List[Dict[str, Any]]:
    """
    Fetch all World Cup 2026 fixtures from API-Football.

    Returns:
        List of fixture dictionaries from API-Football
    """
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {
        "x-rapidapi-key": config.API_FOOTBALL_KEY,
        "x-rapidapi-host": "v3.football.api-sports.io",
    }

    params = {
        "league": 1,  # World Cup
        "season": 2026,
    }

    logger.info("Fetching World Cup 2026 fixtures from API-Football...")

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        fixtures = data.get("response", [])

        logger.info(f"✅ Fetched {len(fixtures)} fixtures from API-Football")
        return fixtures

    except Exception as e:
        logger.error(f"Failed to fetch fixtures: {e}")
        raise


def map_fixtures_to_matches(
    api_fixtures: List[Dict[str, Any]],
    firestore_matches: List[Dict[str, Any]],
    firestore_teams: List[Dict[str, Any]],
) -> Dict[int, Dict[str, Any]]:
    """
    Map API-Football fixtures to Firestore matches by team names.

    Args:
        api_fixtures: Fixtures from API-Football
        firestore_matches: Matches from Firestore
        firestore_teams: Teams from Firestore

    Returns:
        Dictionary mapping Firestore match ID to API-Football fixture data
    """
    logger.info("Mapping API-Football fixtures to Firestore matches...")

    # Team name aliases for API-Football → Firestore mapping
    TEAM_NAME_ALIASES = {
        "Ivory Coast": "Côte d'Ivoire",
        "Iran": "IR Iran",
        "Cape Verde Islands": "Cabo Verde",
    }

    # Create team name lookup (API-Football name → Firestore team)
    team_name_map = {}
    for team in firestore_teams:
        team_name_map[team["name"]] = team

    # Add aliases to map
    for api_name, firestore_name in TEAM_NAME_ALIASES.items():
        if firestore_name in team_name_map:
            team_name_map[api_name] = team_name_map[firestore_name]

    # Map fixtures
    match_fixture_map = {}
    unmatched_fixtures = []

    for fixture in api_fixtures:
        home_team_name = fixture["teams"]["home"]["name"]
        away_team_name = fixture["teams"]["away"]["name"]
        fixture_id = fixture["fixture"]["id"]
        fixture_date = fixture["fixture"]["date"]
        venue_name = fixture["fixture"]["venue"]["name"]
        round_name = fixture["league"]["round"]

        # Find matching Firestore teams
        home_team = team_name_map.get(home_team_name)
        away_team = team_name_map.get(away_team_name)

        if not home_team or not away_team:
            unmatched_fixtures.append(f"{home_team_name} vs {away_team_name}")
            logger.warning(
                f"⚠️  No team mapping for: {home_team_name} vs {away_team_name}"
            )
            continue

        # Find matching Firestore match (check both home/away orders)
        matching_match = None
        for match in firestore_matches:
            # Check exact match
            if (
                match.get("home_team_id") == home_team["id"]
                and match.get("away_team_id") == away_team["id"]
            ):
                matching_match = match
                break
            # Check reversed match (API-Football has teams in opposite order)
            elif (
                match.get("home_team_id") == away_team["id"]
                and match.get("away_team_id") == home_team["id"]
            ):
                matching_match = match
                logger.info(
                    f"⚠️  Found reversed match: {match['home_team_name']} vs {match['away_team_name']} "
                    f"← API has {away_team_name} vs {home_team_name}"
                )
                break

        if matching_match:
            match_fixture_map[matching_match["id"]] = {
                "api_football_fixture_id": fixture_id,
                "kickoff": fixture_date,
                "venue": venue_name,
                "round": round_name,
                "home_team_api_id": fixture["teams"]["home"]["id"],
                "away_team_api_id": fixture["teams"]["away"]["id"],
            }
            logger.info(
                f"✅ Mapped: Match {matching_match['match_number']} - "
                f"{home_team_name} vs {away_team_name} → Fixture {fixture_id}"
            )
        else:
            unmatched_fixtures.append(f"{home_team_name} vs {away_team_name}")
            logger.warning(
                f"⚠️  No Firestore match for: {home_team_name} vs {away_team_name}"
            )

    logger.info(f"✅ Mapped {len(match_fixture_map)} fixtures")

    if unmatched_fixtures:
        logger.warning(f"⚠️  {len(unmatched_fixtures)} fixtures could not be mapped:")
        for fixture in unmatched_fixtures[:10]:
            logger.warning(f"   - {fixture}")

    return match_fixture_map


def update_firestore_matches(
    fs_manager: FirestoreManager, match_fixture_map: Dict[int, Dict[str, Any]]
) -> int:
    """
    Update Firestore matches with API-Football fixture data.

    IMPORTANT: This function also renumbers ALL matches chronologically
    based on API-Football kickoff dates to ensure match numbers reflect
    the authoritative tournament schedule.

    Args:
        fs_manager: Firestore manager
        match_fixture_map: Mapping of match ID to fixture data

    Returns:
        Number of matches updated
    """
    logger.info("Updating Firestore matches with fixture data...")
    logger.info(
        "⚠️  This will renumber ALL matches chronologically based on API-Football dates"
    )

    # Step 1: Update matches with API-Football data
    updated_count = 0

    for match_id, fixture_data in match_fixture_map.items():
        try:
            # Update match in Firestore
            fs_manager.matches_collection.document(str(match_id)).set(
                fixture_data, merge=True
            )

            updated_count += 1

            if updated_count % 10 == 0:
                logger.info(f"   Updated {updated_count} matches...")

        except Exception as e:
            logger.error(f"Failed to update match {match_id}: {e}")

    logger.info(f"✅ Updated {updated_count} matches with API-Football data")

    # Step 2: Renumber ALL matches chronologically
    logger.info("Renumbering matches chronologically...")

    all_matches = fs_manager.get_all_matches()

    # Sort by kickoff date (matches with dates first, then by original match_number)
    def sort_key(match):
        kickoff = match.get("kickoff")
        if kickoff:
            # Has real date from API-Football - use it for sorting
            return (0, kickoff, match.get("match_number", 999))
        else:
            # No date yet - sort after real matches, preserve original order
            return (1, "", match.get("match_number", 999))

    sorted_matches = sorted(all_matches, key=sort_key)

    # Renumber matches chronologically
    renumber_count = 0
    for new_number, match in enumerate(sorted_matches, start=1):
        old_number = match.get("match_number")

        if old_number != new_number:
            try:
                fs_manager.matches_collection.document(str(match["id"])).set(
                    {"match_number": new_number}, merge=True
                )
                renumber_count += 1

                if match.get("kickoff"):
                    logger.info(
                        f"   Renumbered: {match['home_team_name']} vs {match['away_team_name']} "
                        f"(Match #{old_number} → #{new_number}) - {match['kickoff'][:10]}"
                    )
            except Exception as e:
                logger.error(f"Failed to renumber match {match['id']}: {e}")

    logger.info(f"✅ Renumbered {renumber_count} matches chronologically")

    return updated_count


def validate_sync(fs_manager: FirestoreManager) -> None:
    """
    Validate the fixture sync.

    Args:
        fs_manager: Firestore manager
    """
    logger.info("Validating fixture sync...")

    matches = fs_manager.get_all_matches()

    matches_with_fixtures = [m for m in matches if m.get("api_football_fixture_id")]

    group_stage_matches = [m for m in matches if m.get("stage_id") == 1]
    knockout_matches = [m for m in matches if m.get("stage_id") > 1]

    print()
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    print(f"Total matches: {len(matches)}")
    print(f"Matches with API-Football fixture IDs: {len(matches_with_fixtures)}")
    print(f"Group stage matches: {len(group_stage_matches)}")
    print(f"Knockout matches: {len(knockout_matches)}")
    print()

    # Sample some matches
    print("Sample mapped matches:")
    for match in matches_with_fixtures[:5]:
        print(
            f"  - Match {match['match_number']}: {match['home_team_name']} vs {match['away_team_name']}"
        )
        print(f"    Fixture ID: {match.get('api_football_fixture_id')}")
        print(f"    Kickoff: {match.get('kickoff')}")
        print(f"    Venue: {match.get('venue')}")
        print()


def main():
    """Main execution function."""
    print()
    print("=" * 80)
    print("WORLD CUP 2026 FIXTURE SYNC")
    print("=" * 80)
    print()
    print(f"Started: {datetime.now().isoformat()}")
    print()

    # Check configuration
    if not config.API_FOOTBALL_KEY:
        print("❌ ERROR: API_FOOTBALL_KEY not set in environment")
        return False

    print(f"✅ API-Football key configured: {config.API_FOOTBALL_KEY[:10]}...")
    print()

    # Initialize Firestore manager
    try:
        fs_manager = FirestoreManager()
    except Exception as e:
        print(f"❌ Failed to initialize Firestore: {e}")
        return False

    # Step 1: Fetch fixtures from API-Football
    print("-" * 80)
    print("Step 1: Fetching fixtures from API-Football")
    print("-" * 80)
    print()

    try:
        api_fixtures = fetch_wc2026_fixtures()
        print(f"✅ Fetched {len(api_fixtures)} fixtures")
        print()
    except Exception as e:
        print(f"❌ Failed to fetch fixtures: {e}")
        return False

    # Step 2: Load Firestore data
    print("-" * 80)
    print("Step 2: Loading Firestore data")
    print("-" * 80)
    print()

    try:
        firestore_matches = fs_manager.get_all_matches()
        firestore_teams = fs_manager.get_all_teams()

        print(f"✅ Loaded {len(firestore_matches)} matches")
        print(f"✅ Loaded {len(firestore_teams)} teams")
        print()
    except Exception as e:
        print(f"❌ Failed to load Firestore data: {e}")
        return False

    # Step 3: Map fixtures to matches
    print("-" * 80)
    print("Step 3: Mapping fixtures to matches")
    print("-" * 80)
    print()

    try:
        match_fixture_map = map_fixtures_to_matches(
            api_fixtures, firestore_matches, firestore_teams
        )
        print(f"✅ Mapped {len(match_fixture_map)} fixtures")
        print()
    except Exception as e:
        print(f"❌ Failed to map fixtures: {e}")
        return False

    # Step 4: Update Firestore
    print("-" * 80)
    print("Step 4: Updating Firestore")
    print("-" * 80)
    print()

    try:
        updated_count = update_firestore_matches(fs_manager, match_fixture_map)
        print(f"✅ Updated {updated_count} matches")
        print()
    except Exception as e:
        print(f"❌ Failed to update Firestore: {e}")
        return False

    # Step 5: Validate
    print("-" * 80)
    print("Step 5: Validating sync")
    print("-" * 80)
    print()

    try:
        validate_sync(fs_manager)
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False

    # Success
    print("=" * 80)
    print("✅ FIXTURE SYNC COMPLETE!")
    print("=" * 80)
    print()
    print(f"Finished: {datetime.now().isoformat()}")
    print()

    return True


if __name__ == "__main__":
    try:
        success = main()

        if success:
            print("✅ Fixture sync completed successfully")
            sys.exit(0)
        else:
            print("❌ Fixture sync failed")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Script interrupted by user")
        sys.exit(1)

    except Exception as e:
        logger.error(f"Script failed with exception: {e}")
        print(f"\n❌ Script failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
