import sqlite3
from dataclasses import dataclass
from typing import List, Optional
import os


@dataclass
class Team:
    id: int
    name: str
    fifa_code: str
    group_letter: str
    is_placeholder: bool
    api_football_id: Optional[int] = None


@dataclass
class Match:
    id: int
    match_number: int
    home_team_id: Optional[int]
    away_team_id: Optional[int]
    venue: str
    stage_id: int
    kickoff_at: str
    match_label: str


class DBManager:
    def __init__(self, db_path: str):
        if not os.path.exists(db_path):
            # SQLite creates a new file if it doesn't exist, but our tests expect an error
            # for invalid paths to verify graceful handling/validation.
            raise Exception(f"Database file not found at {db_path}")
        self.db_path = db_path

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def load_all_teams(self) -> List[Team]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, team_name, fifa_code, group_letter, is_placeholder, api_football_id FROM teams"
            )
            rows = cursor.fetchall()
            return [
                Team(
                    id=row["id"],
                    name=row["team_name"],
                    fifa_code=row["fifa_code"],
                    group_letter=row["group_letter"],
                    is_placeholder=bool(row["is_placeholder"]),
                    api_football_id=row["api_football_id"],
                )
                for row in rows
            ]

    def load_all_matches(self) -> List[Match]:
        query = """
            SELECT m.id, m.match_number, m.home_team_id, m.away_team_id, 
                   c.venue_name as venue, m.stage_id, m.kickoff_at, m.match_label
            FROM matches m
            JOIN host_cities c ON m.city_id = c.id
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [
                Match(
                    id=row["id"],
                    match_number=row["match_number"],
                    home_team_id=row["home_team_id"],
                    away_team_id=row["away_team_id"],
                    venue=row["venue"],
                    stage_id=row["stage_id"],
                    kickoff_at=row["kickoff_at"],
                    match_label=row["match_label"],
                )
                for row in rows
            ]

    def load_group_teams(self, group_letter: str) -> List[Team]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, team_name, fifa_code, group_letter, is_placeholder, api_football_id FROM teams WHERE group_letter = ?",
                (group_letter,),
            )
            rows = cursor.fetchall()
            return [
                Team(
                    id=row["id"],
                    name=row["team_name"],
                    fifa_code=row["fifa_code"],
                    group_letter=row["group_letter"],
                    is_placeholder=bool(row["is_placeholder"]),
                    api_football_id=row["api_football_id"],
                )
                for row in rows
            ]

    def load_knockout_matches(self) -> List[Match]:
        return self.load_matches_by_stage_range(min_stage_id=2)

    def load_matches_by_stage(self, stage_id: int) -> List[Match]:
        query = """
            SELECT m.id, m.match_number, m.home_team_id, m.away_team_id, 
                   c.venue_name as venue, m.stage_id, m.kickoff_at, m.match_label
            FROM matches m
            JOIN host_cities c ON m.city_id = c.id
            WHERE m.stage_id = ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (stage_id,))
            rows = cursor.fetchall()
            return [
                Match(
                    id=row["id"],
                    match_number=row["match_number"],
                    home_team_id=row["home_team_id"],
                    away_team_id=row["away_team_id"],
                    venue=row["venue"],
                    stage_id=row["stage_id"],
                    kickoff_at=row["kickoff_at"],
                    match_label=row["match_label"],
                )
                for row in rows
            ]

    def load_matches_by_stage_range(self, min_stage_id: int) -> List[Match]:
        query = """
            SELECT m.id, m.match_number, m.home_team_id, m.away_team_id, 
                   c.venue_name as venue, m.stage_id, m.kickoff_at, m.match_label
            FROM matches m
            JOIN host_cities c ON m.city_id = c.id
            WHERE m.stage_id >= ?
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (min_stage_id,))
            rows = cursor.fetchall()
            return [
                Match(
                    id=row["id"],
                    match_number=row["match_number"],
                    home_team_id=row["home_team_id"],
                    away_team_id=row["away_team_id"],
                    venue=row["venue"],
                    stage_id=row["stage_id"],
                    kickoff_at=row["kickoff_at"],
                    match_label=row["match_label"],
                )
                for row in rows
            ]
