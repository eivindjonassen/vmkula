"""
One-time migration script: SQLite → Firestore

Migrates all data from worldcup2026.db to Firestore collections.

Collections created:
- teams: All 48 teams with API-Football IDs
- matches: All 104 matches with venue info
- host_cities: All 16 host cities

Usage:
    python migrate_to_firestore.py

Backup:
    cp worldcup2026.db worldcup2026.db.backup
"""

import logging
import sys
import sqlite3
from datetime import datetime

from src.db_manager import DBManager
from src.firestore_manager import FirestoreManager, Team, Match

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def migrate():
    """Migrate all data from SQLite to Firestore."""

    print("=" * 80)
    print("MIGRATION: SQLite → Firestore")
    print("=" * 80)
    print()

    # Initialize managers
    sqlite_db = DBManager("worldcup2026.db")
    firestore_db = FirestoreManager()

    # Step 1: Migrate host cities
    print("-" * 80)
    print("Step 1: Migrating host cities...")
    print("-" * 80)

    try:
        # Query cities directly from SQLite
        conn = sqlite3.connect("worldcup2026.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM host_cities")
        city_rows = cursor.fetchall()
        conn.close()

        logger.info(f"Found {len(city_rows)} cities in SQLite")

        for city in city_rows:
            firestore_db.create_city(
                city_id=city["id"],
                city_name=city["city_name"],
                country=city["country"],
                venue_name=city["venue_name"],
                region_cluster=city["region_cluster"]
                if "region_cluster" in city.keys()
                else None,
                airport_code=city["airport_code"]
                if "airport_code" in city.keys()
                else None,
            )
            print(f"  ✅ Migrated: {city['city_name']} - {city['venue_name']}")

        print(f"\n✅ Migrated {len(city_rows)} cities\n")

    except Exception as e:
        logger.error(f"Failed to migrate cities: {e}")
        print(f"❌ Cities migration failed: {e}")
        return False

    # Step 2: Migrate teams
    print("-" * 80)
    print("Step 2: Migrating teams...")
    print("-" * 80)

    try:
        teams = sqlite_db.load_all_teams()
        logger.info(f"Found {len(teams)} teams in SQLite")

        teams_with_api = 0

        for team in teams:
            firestore_team = Team(
                id=team.id,
                name=team.name,
                fifa_code=team.fifa_code,
                group=team.group_letter,
                api_football_id=team.api_football_id,
                is_placeholder=bool(team.is_placeholder),
            )

            firestore_db.create_team(firestore_team)

            if team.api_football_id:
                teams_with_api += 1
                print(
                    f"  ✅ {team.name} (Group {team.group_letter}) - API ID: {team.api_football_id}"
                )
            else:
                print(f"  ⚠️  {team.name} (Group {team.group_letter}) - No API ID")

        print(f"\n✅ Migrated {len(teams)} teams")
        print(f"   - {teams_with_api} teams with API-Football IDs")
        print(f"   - {len(teams) - teams_with_api} teams without API IDs\n")

    except Exception as e:
        logger.error(f"Failed to migrate teams: {e}")
        print(f"❌ Teams migration failed: {e}")
        return False

    # Step 3: Migrate matches
    print("-" * 80)
    print("Step 3: Migrating matches...")
    print("-" * 80)

    try:
        matches = sqlite_db.load_all_matches()
        logger.info(f"Found {len(matches)} matches in SQLite")

        # Create team lookup
        team_lookup = {team.id: team for team in teams}

        # Get city lookup
        conn = sqlite3.connect("worldcup2026.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT m.id as match_id, c.* FROM matches m JOIN host_cities c ON m.city_id = c.id"
        )
        city_data = {row["match_id"]: row for row in cursor.fetchall()}
        conn.close()

        for match in matches:
            # Get team names
            home_team = (
                team_lookup.get(match.home_team_id) if match.home_team_id else None
            )
            away_team = (
                team_lookup.get(match.away_team_id) if match.away_team_id else None
            )

            # Get city info
            city_info = city_data.get(match.id)

            firestore_match = Match(
                id=match.id,
                match_number=match.match_number,
                home_team_id=match.home_team_id,
                away_team_id=match.away_team_id,
                home_team_name=home_team.name if home_team else "TBD",
                away_team_name=away_team.name if away_team else "TBD",
                city=city_info["city_name"] if city_info else "TBD",
                venue=match.venue,  # Already from JOIN in load_all_matches
                stage_id=match.stage_id,
                kickoff=match.kickoff_at,
                label=match.match_label,
                api_football_fixture_id=None,  # Will be added later
            )

            firestore_db.create_match(firestore_match)

            if match.match_number % 10 == 0:
                print(f"  ✅ Migrated matches 1-{match.match_number}...")

        print(f"\n✅ Migrated {len(matches)} matches\n")

    except Exception as e:
        logger.error(f"Failed to migrate matches: {e}")
        print(f"❌ Matches migration failed: {e}")
        return False

    # Step 4: Verify migration
    print("-" * 80)
    print("Step 4: Verifying migration...")
    print("-" * 80)

    try:
        fs_teams = firestore_db.get_all_teams()
        fs_matches = firestore_db.get_all_matches()

        print(f"  Teams in Firestore: {len(fs_teams)}")
        print(f"  Matches in Firestore: {len(fs_matches)}")

        if len(fs_teams) != len(teams):
            print(
                f"  ⚠️  Team count mismatch! SQLite: {len(teams)}, Firestore: {len(fs_teams)}"
            )
            return False

        if len(fs_matches) != len(matches):
            print(
                f"  ⚠️  Match count mismatch! SQLite: {len(matches)}, Firestore: {len(fs_matches)}"
            )
            return False

        print(f"\n✅ Verification passed!\n")

    except Exception as e:
        logger.error(f"Verification failed: {e}")
        print(f"❌ Verification failed: {e}")
        return False

    # Summary
    print("=" * 80)
    print("MIGRATION COMPLETE!")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  ✅ {len(city_rows)} host cities migrated")
    print(f"  ✅ {len(teams)} teams migrated ({teams_with_api} with API-Football IDs)")
    print(f"  ✅ {len(matches)} matches migrated")
    print()
    print("Next steps:")
    print("  1. Test the application with Firestore")
    print("  2. Run predictions to populate team stats")
    print("  3. Verify frontend displays correctly")
    print("  4. Remove worldcup2026.db when confident")
    print()
    print("Backup command:")
    print("  cp backend/worldcup2026.db backend/worldcup2026.db.backup")
    print()

    return True


if __name__ == "__main__":
    try:
        success = migrate()

        if success:
            sys.exit(0)
        else:
            print("\n❌ Migration failed!")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Migration failed with exception: {e}")
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
