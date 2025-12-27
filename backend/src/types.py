"""
Type definitions for vmkula backend.

Dataclasses for teams and matches used throughout the backend.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Team:
    """Represents a national team in the tournament."""

    id: int
    name: str
    fifa_code: str
    group_letter: str
    is_placeholder: bool
    api_football_id: Optional[int] = None


@dataclass
class Match:
    """Represents a fixture in the tournament."""

    id: int
    match_number: int
    home_team_id: Optional[int]
    away_team_id: Optional[int]
    venue: str
    stage_id: int
    kickoff_at: str
    match_label: str
