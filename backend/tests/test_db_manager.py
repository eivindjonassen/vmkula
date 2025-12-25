"""Tests for db_manager.py - SQLite database interface

These tests are expected to FAIL until T017 (db_manager implementation) is complete.
Following TDD Red-Green-Refactor cycle.
"""

import pytest
from pathlib import Path


# Expected to fail - DBManager not yet implemented
def test_load_all_teams_returns_48_teams():
    """Test that load_all_teams() returns all 48 World Cup teams"""
    from src.db_manager import DBManager

    db_path = Path(__file__).parent.parent / "worldcup2026.db"
    db = DBManager(str(db_path))

    teams = db.load_all_teams()

    assert len(teams) == 48, f"Expected 48 teams, got {len(teams)}"

    # Verify schema
    first_team = teams[0]
    assert hasattr(first_team, "id"), "Team should have 'id' attribute"
    assert hasattr(first_team, "name"), "Team should have 'name' attribute"
    assert hasattr(first_team, "fifa_code"), "Team should have 'fifa_code' attribute"
    assert hasattr(first_team, "group_letter"), (
        "Team should have 'group_letter' attribute"
    )


def test_load_all_matches_returns_104_matches():
    """Test that load_all_matches() returns all 104 tournament matches"""
    from src.db_manager import DBManager

    db_path = Path(__file__).parent.parent / "worldcup2026.db"
    db = DBManager(str(db_path))

    matches = db.load_all_matches()

    assert len(matches) == 104, f"Expected 104 matches, got {len(matches)}"

    # Verify relationships
    first_match = matches[0]
    assert hasattr(first_match, "home_team_id"), "Match should have 'home_team_id'"
    assert hasattr(first_match, "away_team_id"), "Match should have 'away_team_id'"
    assert hasattr(first_match, "venue"), "Match should have 'venue' (city name)"
    assert hasattr(first_match, "stage_id"), "Match should have 'stage_id'"


def test_load_group_teams_returns_4_teams_for_group_a():
    """Test that load_group_teams('A') returns exactly 4 teams"""
    from src.db_manager import DBManager

    db_path = Path(__file__).parent.parent / "worldcup2026.db"
    db = DBManager(str(db_path))

    group_a_teams = db.load_group_teams("A")

    assert len(group_a_teams) == 4, (
        f"Group A should have 4 teams, got {len(group_a_teams)}"
    )

    # Verify all teams are in Group A
    for team in group_a_teams:
        assert team.group_letter == "A", f"Team {team.name} should be in Group A"


def test_load_knockout_matches_returns_32_matches():
    """Test that load_knockout_matches() returns 32 knockout stage matches (stage_id >= 2)"""
    from src.db_manager import DBManager

    db_path = Path(__file__).parent.parent / "worldcup2026.db"
    db = DBManager(str(db_path))

    knockout_matches = db.load_knockout_matches()

    assert len(knockout_matches) == 32, (
        f"Expected 32 knockout matches, got {len(knockout_matches)}"
    )

    # Verify all matches are knockout stage (stage_id >= 2)
    for match in knockout_matches:
        assert match.stage_id >= 2, (
            f"Match {match.match_number} should be knockout (stage_id >= 2)"
        )


def test_database_connection_error_handling():
    """Test that DBManager handles invalid database paths gracefully"""
    from src.db_manager import DBManager

    with pytest.raises(Exception) as exc_info:
        db = DBManager("/invalid/path/to/database.db")
        db.load_all_teams()  # Should fail with connection error

    # Verify error message is meaningful
    assert (
        "database" in str(exc_info.value).lower()
        or "connection" in str(exc_info.value).lower()
    )


def test_load_matches_by_stage_id():
    """Test querying matches by specific stage_id"""
    from src.db_manager import DBManager

    db_path = Path(__file__).parent.parent / "worldcup2026.db"
    db = DBManager(str(db_path))

    # Assuming stage_id=1 is group stage with 72 matches (12 groups * 6 matches)
    group_stage_matches = db.load_matches_by_stage(stage_id=1)

    assert len(group_stage_matches) == 72, (
        f"Expected 72 group stage matches, got {len(group_stage_matches)}"
    )

    # Verify all returned matches have stage_id=1
    for match in group_stage_matches:
        assert match.stage_id == 1, f"Match {match.match_number} should have stage_id=1"
