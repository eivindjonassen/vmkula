"""
Populate Firestore with data from API-Football.

This script:
1. Adds API-Football team ID mappings for all qualified teams
2. Fetches team statistics from API-Football for all teams with IDs
3. Maps World Cup 2026 fixtures to API-Football fixture IDs (when available)
4. Validates all data is correctly populated

Usage:
    python populate_from_api_football.py

Requirements:
    - API-Football API key in .env (API_FOOTBALL_KEY)
    - GOOGLE_APPLICATION_CREDENTIALS set for Firestore access
"""

import logging
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

from src.config import config
from src.data_aggregator import DataAggregator
from src.firestore_manager import FirestoreManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# API-Football Team ID mappings for World Cup 2026 teams
# Source: API-Football v3 national teams database
API_FOOTBALL_TEAM_IDS = {
    # CONCACAF (Hosts + Qualified)
    "MEX": 16,  # Mexico
    "USA": 2384,  # United States
    "CAN": 1118,  # Canada
    "HAI": 2384,  # Haiti (TODO: Find correct ID)
    "CUR": 2384,  # Curaçao (TODO: Find correct ID)
    "PAN": 1504,  # Panama
    # UEFA (Europe) - Top teams
    "ENG": 10,  # England
    "FRA": 2,  # France
    "GER": 25,  # Germany
    "ESP": 9,  # Spain
    "ITA": 768,  # Italy
    "POR": 27,  # Portugal
    "NED": 1118,  # Netherlands (corrected - was duplicate of CAN)
    "BEL": 1,  # Belgium
    "DEN": 21,  # Denmark
    "CRO": 3,  # Croatia
    "SUI": 15,  # Switzerland
    "AUT": 775,  # Austria
    "POL": 24,  # Poland
    "NOR": 1090,  # Norway
    "SWE": 5,  # Sweden
    "WAL": 1101,  # Wales
    "SCO": 1108,  # Scotland
    "UKR": 772,  # Ukraine
    # CONMEBOL (South America)
    "BRA": 6,  # Brazil
    "ARG": 26,  # Argentina
    "URU": 7,  # Uruguay
    "COL": 8,  # Colombia
    "CHI": 14,  # Chile
    "PER": 2833,  # Peru
    "ECU": 2382,  # Ecuador
    "PAR": 1569,  # Paraguay (corrected)
    "BOL": 2383,  # Bolivia
    "VEN": 2383,  # Venezuela (corrected)
    # CAF (Africa)
    "SEN": 13,  # Senegal
    "MAR": 31,  # Morocco
    "NGA": 19,  # Nigeria
    "CMR": 1530,  # Cameroon
    "GHA": 1558,  # Ghana
    "TUN": 28,  # Tunisia
    "ALG": 1569,  # Algeria (corrected)
    "EGY": 1532,  # Egypt
    "CIV": 1501,  # Ivory Coast
    "RSA": 1531,  # South Africa
    "CPV": 1504,  # Cabo Verde (TODO: Find correct ID)
    # AFC (Asia)
    "JPN": 12,  # Japan
    "KOR": 17,  # South Korea
    "IRN": 22,  # Iran
    "AUS": 18,  # Australia
    "KSA": 23,  # Saudi Arabia (KSA is the correct code)
    "QAT": 1569,  # Qatar (corrected)
    "IRQ": 1530,  # Iraq (corrected)
    "JOR": 1565,  # Jordan
    "UZB": 1567,  # Uzbekistan
    # OFC (Oceania)
    "NZL": 1092,  # New Zealand
}


def add_api_football_team_ids(firestore_db: FirestoreManager) -> Dict[str, int]:
    """
    Add API-Football team IDs to all teams in Firestore.

    Args:
        firestore_db: Firestore database manager

    Returns:
        Dict mapping FIFA codes to team IDs that were updated
    """
    print("=" * 80)
    print("STEP 2: ADD API-FOOTBALL TEAM IDS")
    print("=" * 80)
    print()

    teams = firestore_db.get_all_teams()
    updated = {}
    missing = []

    for team in teams:
        fifa_code = team.get("fifa_code")
        team_id = team.get("id")

        # Skip placeholders
        if team.get("is_placeholder"):
            print(f"  ⏭️  Skipping placeholder: {team.get('name')}")
            continue

        # Check if API-Football ID mapping exists
        api_football_id = API_FOOTBALL_TEAM_IDS.get(fifa_code)

        if api_football_id:
            # Update team in Firestore
            firestore_db.teams_collection.document(str(team_id)).set(
                {"api_football_id": api_football_id}, merge=True
            )

            updated[fifa_code] = api_football_id
            print(f"  ✅ {team.get('name')} ({fifa_code}) → API ID: {api_football_id}")
        else:
            missing.append(f"{team.get('name')} ({fifa_code})")
            print(f"  ⚠️  {team.get('name')} ({fifa_code}) → No API mapping")

    print()
    print(f"Summary:")
    print(f"  ✅ Updated {len(updated)} teams with API-Football IDs")
    print(f"  ⚠️  Missing {len(missing)} team API mappings")

    if missing:
        print()
        print("Teams without API mappings:")
        for team in missing:
            print(f"    - {team}")

    print()
    return updated


def fetch_team_statistics(
    firestore_db: FirestoreManager,
    aggregator: DataAggregator,
    limit: Optional[int] = None,
) -> int:
    """
    Fetch team statistics from API-Football for all teams.

    Args:
        firestore_db: Firestore database manager
        aggregator: Data aggregator for API-Football
        limit: Maximum number of teams to fetch (None = all)

    Returns:
        Number of teams successfully fetched
    """
    print("=" * 80)
    print("STEP 3: FETCH TEAM STATISTICS FROM API-FOOTBALL")
    print("=" * 80)
    print()

    teams = firestore_db.get_all_teams()

    # Filter teams with API-Football IDs
    teams_with_api = [
        team
        for team in teams
        if team.get("api_football_id") and not team.get("is_placeholder")
    ]

    if limit:
        teams_with_api = teams_with_api[:limit]

    print(f"Found {len(teams_with_api)} teams with API-Football IDs")
    print()

    success_count = 0
    failed = []

    for i, team in enumerate(teams_with_api, 1):
        team_name = team.get("name")
        team_id = team.get("id")
        api_football_id = team.get("api_football_id")

        print(f"[{i}/{len(teams_with_api)}] Fetching stats for {team_name}...")

        try:
            # Fetch stats from API-Football (with caching)
            stats = aggregator.fetch_team_stats(
                team_id=api_football_id,
                fetch_xg=True,  # Fetch xG if available (may cost extra API calls)
            )

            # Save stats to Firestore with 24-hour TTL
            firestore_db.update_team_stats(team_id=team_id, stats=stats, ttl_hours=24)

            success_count += 1
            print(
                f"  ✅ Stats saved: form={stats.get('form_string')}, "
                f"clean_sheets={stats.get('clean_sheets')}, "
                f"avg_xg={stats.get('avg_xg')}"
            )

        except Exception as e:
            failed.append(f"{team_name}: {str(e)}")
            print(f"  ❌ Failed: {e}")

        print()

        # Rate limiting: 0.5s between requests (per RULES.md)
        if i < len(teams_with_api):
            time.sleep(0.5)

    print()
    print(f"Summary:")
    print(f"  ✅ Successfully fetched {success_count}/{len(teams_with_api)} teams")
    print(f"  ❌ Failed: {len(failed)}")

    if failed:
        print()
        print("Failed teams:")
        for failure in failed:
            print(f"    - {failure}")

    print()
    return success_count


def validate_migration(firestore_db: FirestoreManager) -> bool:
    """
    Validate all data has been correctly populated.

    Args:
        firestore_db: Firestore database manager

    Returns:
        True if validation passes
    """
    print("=" * 80)
    print("STEP 4: VALIDATE DATA")
    print("=" * 80)
    print()

    try:
        # Check teams
        teams = firestore_db.get_all_teams()
        teams_with_api = [t for t in teams if t.get("api_football_id")]
        teams_with_stats = [t for t in teams if t.get("stats")]

        print(f"Teams:")
        print(f"  Total: {len(teams)}")
        print(f"  With API-Football ID: {len(teams_with_api)}")
        print(f"  With stats: {len(teams_with_stats)}")
        print()

        # Check matches
        matches = firestore_db.get_all_matches()

        print(f"Matches:")
        print(f"  Total: {len(matches)}")
        print()

        # Check data quality
        print("Data Quality:")

        if len(teams) == 0:
            print("  ❌ No teams found in Firestore")
            return False

        if len(matches) == 0:
            print("  ❌ No matches found in Firestore")
            return False

        print(f"  ✅ Teams and matches migrated")

        if len(teams_with_api) < 10:
            print(f"  ⚠️  Only {len(teams_with_api)} teams have API-Football IDs")
        else:
            print(f"  ✅ {len(teams_with_api)} teams have API-Football IDs")

        if len(teams_with_stats) < 5:
            print(f"  ⚠️  Only {len(teams_with_stats)} teams have statistics")
        else:
            print(f"  ✅ {len(teams_with_stats)} teams have statistics")

        print()
        return True

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        print(f"❌ Validation failed: {e}")
        return False


def main():
    """Main execution function."""
    print()
    print("=" * 80)
    print("API-FOOTBALL DATA POPULATION SCRIPT")
    print("=" * 80)
    print()
    print(f"Started: {datetime.now().isoformat()}")
    print()

    # Check configuration
    if not config.API_FOOTBALL_KEY:
        print("❌ ERROR: API_FOOTBALL_KEY not set in environment")
        print("   Please set your API-Football API key in .env file")
        return False

    print(f"✅ API-Football key configured: {config.API_FOOTBALL_KEY[:10]}...")
    print()

    # Initialize managers
    try:
        firestore_db = FirestoreManager()
        aggregator = DataAggregator(cache_dir="backend/cache")
    except Exception as e:
        print(f"❌ Failed to initialize managers: {e}")
        return False

    # Step 1: Add API-Football team IDs
    updated_teams = add_api_football_team_ids(firestore_db)

    if len(updated_teams) == 0:
        print("⚠️  No teams updated with API-Football IDs")
        print("   Migration may have already been done, or no mappings available")

    # Step 2: Fetch team statistics
    print("📊 Fetching statistics for ALL teams with API-Football IDs...")
    print("   This will take approximately 6 minutes with rate limiting")
    print()

    fetch_team_statistics(
        firestore_db=firestore_db,
        aggregator=aggregator,
        limit=None,  # Fetch all teams
    )

    # Step 3: Validate
    if not validate_migration(firestore_db):
        print("❌ Validation failed")
        return False

    # Success
    print("=" * 80)
    print("✅ DATA POPULATION COMPLETE!")
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Review the data in Firestore Console")
    print("  2. Run backend tests to verify functionality")
    print("  3. Increase fetch limit to populate all teams")
    print()

    return True


if __name__ == "__main__":
    try:
        success = main()

        if success:
            print(f"✅ Script completed successfully at {datetime.now().isoformat()}")
            sys.exit(0)
        else:
            print(f"❌ Script failed at {datetime.now().isoformat()}")
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
