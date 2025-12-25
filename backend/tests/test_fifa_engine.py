import pytest
from src.fifa_engine import FifaEngine


def test_calculate_standings_basic_points():
    """Test basic standings: 3 points for win, 1 for draw, 0 for loss."""
    engine = FifaEngine()
    # Scenario: Team A wins, Team B loses, Team C & D draw
    results = [
        {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_score": 2,
            "away_score": 0,
        },
        {
            "home_team": "Team C",
            "away_team": "Team D",
            "home_score": 1,
            "away_score": 1,
        },
    ]
    standings = engine.calculate_standings("A", results)

    # Sort by points to check order
    teams = {s.team_name: s for s in standings}

    assert teams["Team A"].points == 3
    assert teams["Team B"].points == 0
    assert teams["Team C"].points == 1
    assert teams["Team D"].points == 1


def test_goal_difference_calculation():
    """Test goal difference calculation (goals_for - goals_against)."""
    engine = FifaEngine()
    results = [
        {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_score": 3,
            "away_score": 1,
        },
    ]
    standings = engine.calculate_standings("A", results)
    teams = {s.team_name: s for s in standings}

    assert teams["Team A"].goals_for == 3
    assert teams["Team A"].goals_against == 1
    assert teams["Team A"].goal_difference == 2

    assert teams["Team B"].goals_for == 1
    assert teams["Team B"].goals_against == 3
    assert teams["Team B"].goal_difference == -2


def test_sorting_criteria():
    """Test sorting by points, then GD, then goals scored."""
    engine = FifaEngine()
    # Teams with same points, different GD
    # Teams with same points and GD, different goals scored
    results = [
        {
            "home_team": "Team A",
            "away_team": "Team B",
            "home_score": 1,
            "away_score": 0,
        },  # A: 3pts, +1 GD, 1 GF
        {
            "home_team": "Team C",
            "away_team": "Team D",
            "home_score": 2,
            "away_score": 1,
        },  # C: 3pts, +1 GD, 2 GF
        {
            "home_team": "Team E",
            "away_team": "Team F",
            "home_score": 3,
            "away_score": 0,
        },  # E: 3pts, +3 GD, 3 GF
    ]
    # We need to provide all teams in the group to the engine if it doesn't know them
    standings = engine.calculate_standings("A", results)

    # Expected order: E (GD +3), C (GD +1, GF 2), A (GD +1, GF 1)
    assert standings[0].team_name == "Team E"
    assert standings[1].team_name == "Team C"
    assert standings[2].team_name == "Team A"


def test_fair_play_points_calculation():
    """Test Fair Play Points calculation (yellow=-1, 2nd yellow=-3, red=-4)."""
    engine = FifaEngine()
    # Team A: 1 yellow (-1)
    # Team B: 1 red (-4)
    # Team C: 1 yellow + 2nd yellow (-3)
    # Team D: clean (0)

    # We might need a way to pass cards to calculate_standings
    results = []  # No matches
    cards = [
        {"team_name": "Team A", "yellow": 1, "red": 0, "second_yellow": 0},
        {"team_name": "Team B", "yellow": 0, "red": 1, "second_yellow": 0},
        {"team_name": "Team C", "yellow": 1, "red": 0, "second_yellow": 1},
        {"team_name": "Team D", "yellow": 0, "red": 0, "second_yellow": 0},
    ]

    # Assuming interface allows passing card data
    standings = engine.calculate_standings("A", results, cards=cards)
    teams = {s.team_name: s for s in standings}

    assert teams["Team A"].fair_play_points == -1
    assert teams["Team B"].fair_play_points == -4
    assert teams["Team C"].fair_play_points == -3
    assert teams["Team D"].fair_play_points == 0


def test_tiebreaker_with_fair_play():
    """
    CRITICAL TEST: Tiebreaker with Fair Play Points.
    Scenario: Mexico and Poland both have 4 points, +1 GD, 3 GF.
    Mexico: 1 yellow card = -1 fair play point.
    Poland: 1 red card = -4 fair play points.
    Expected: Mexico ranks higher.
    """
    engine = FifaEngine()
    results = [
        {
            "home_team": "Mexico",
            "away_team": "Poland",
            "home_score": 0,
            "away_score": 0,
        },
        {
            "home_team": "Mexico",
            "away_team": "Team C",
            "home_score": 2,
            "away_score": 1,
        },
        {
            "home_team": "Poland",
            "away_team": "Team C",
            "home_score": 2,
            "away_score": 1,
        },
        {
            "home_team": "Team D",
            "away_team": "Mexico",
            "home_score": 1,
            "away_score": 1,
        },
        {
            "home_team": "Team D",
            "away_team": "Poland",
            "home_score": 1,
            "away_score": 1,
        },
    ]
    # Mexico: Draw, Win, Draw = 5 pts. GD: +1 (2-1), +0 (1-1) = +1. GF: 3.
    # Poland: Draw, Win, Draw = 5 pts. GD: +1, GF: 3.

    cards = [
        {"team_name": "Mexico", "yellow": 1, "red": 0, "second_yellow": 0},  # -1
        {"team_name": "Poland", "yellow": 0, "red": 1, "second_yellow": 0},  # -4
    ]

    standings = engine.calculate_standings("C", results, cards=cards)

    # Find Mexico and Poland in standings
    mexico_rank = next(i for i, s in enumerate(standings) if s.team_name == "Mexico")
    poland_rank = next(i for i, s in enumerate(standings) if s.team_name == "Poland")

    assert mexico_rank < poland_rank


def test_deterministic_fallback():
    """Test deterministic fallback (hash-based tiebreaker) when all criteria equal."""
    engine = FifaEngine()
    # All stats identical, including fair play
    results = []
    cards = []

    # Two teams with identical names? No, different names but identical stats.
    # The tiebreaker should be deterministic based on team name.

    standings1 = engine.calculate_standings("A", results, cards=cards)
    standings2 = engine.calculate_standings("A", results, cards=cards)

    assert [s.team_name for s in standings1] == [s.team_name for s in standings2]


def test_rank_third_place_teams():
    """
    Test ranking of 12 third-place teams across all groups.
    Top 8 selection criteria: points, GD, goals, fair play.
    """
    engine = FifaEngine()

    # Mock standings from 12 groups (A-L)
    # Each list contains the 3rd place team from that group
    mock_standings = {}

    # 12 teams with various stats
    # We'll create a helper to generate GroupStanding-like objects if needed,
    # but for now we'll assume FifaEngine.rank_third_place_teams takes a dict of standings

    # Creating 12 teams, we want to select top 8.
    # Teams 1-8: Stronger
    # Teams 9-12: Weaker

    from dataclasses import dataclass

    @dataclass
    class MockStanding:
        team_name: str
        group_letter: str
        rank: int
        points: int
        goal_difference: int
        goals_for: int
        fair_play_points: int

    third_place_candidates = [
        MockStanding("Team A3", "A", 3, 4, 1, 3, 0),  # 1
        MockStanding("Team B3", "B", 3, 4, 1, 2, 0),  # 2
        MockStanding("Team C3", "C", 3, 4, 0, 3, 0),  # 3
        MockStanding("Team D3", "D", 3, 3, 2, 4, 0),  # 4
        MockStanding("Team E3", "E", 3, 3, 1, 3, 0),  # 5
        MockStanding("Team F3", "F", 3, 3, 1, 2, 0),  # 6
        MockStanding("Team G3", "G", 3, 3, 1, 2, -1),  # 7 (fair play)
        MockStanding("Team H3", "H", 3, 3, 1, 2, -4),  # 8 (fair play)
        MockStanding("Team I3", "I", 3, 2, 0, 2, 0),  # Out
        MockStanding("Team J3", "J", 3, 1, -1, 1, 0),  # Out
        MockStanding("Team K3", "K", 3, 1, -2, 0, 0),  # Out
        MockStanding("Team L3", "L", 3, 0, -3, 0, 0),  # Out
    ]

    # Constructing the full standings dict expected by the method
    # Actually, the method might just need the list of 3rd place teams or the full standings
    # Task says: rank_third_place_teams(standings)

    # If it takes the full standings dict:
    full_standings = {
        chr(65 + i): [None, None, third_place_candidates[i]] for i in range(12)
    }

    qualified = engine.rank_third_place_teams(full_standings)

    assert len(qualified) == 8
    assert qualified[0].team_name == "Team A3"
    assert qualified[7].team_name == "Team H3"
    assert "Team I3" not in [q.team_name for q in qualified]


def test_third_place_deterministic_fallback():
    """Test edge case: multiple teams with identical records (use deterministic seed)."""
    engine = FifaEngine()

    from dataclasses import dataclass

    @dataclass
    class MockStanding:
        team_name: str
        group_letter: str
        rank: int
        points: int
        goal_difference: int
        goals_for: int
        fair_play_points: int

    # Teams with identical stats
    third_place_candidates = [
        MockStanding("Team X", "A", 3, 3, 0, 2, 0),
        MockStanding("Team Y", "B", 3, 3, 0, 2, 0),
    ]

    full_standings = {
        "A": [None, None, third_place_candidates[0]],
        "B": [None, None, third_place_candidates[1]],
    }

    # We only want top 1 for this test to check deterministic selection
    # But the method returns top 8. We'll check if the order is consistent.

    qualified1 = engine.rank_third_place_teams(full_standings)
    qualified2 = engine.rank_third_place_teams(full_standings)

    assert [q.team_name for q in qualified1] == [q.team_name for q in qualified2]
