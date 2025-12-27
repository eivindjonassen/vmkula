"""
Firestore data management for teams, matches, and predictions.

Replaces SQLite database with Firestore as the single source of truth.

Features:
- Smart caching with TTL (24 hours for team stats)
- Change detection for predictions (only regenerate when stats change)
- Automatic cache expiration
- Hash-based change detection
"""

import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from google.cloud import firestore
from src.config import config

logger = logging.getLogger(__name__)


@dataclass
class Team:
    """Team data model."""

    id: int
    name: str
    fifa_code: str
    group: str
    api_football_id: Optional[int] = None
    is_placeholder: bool = False


@dataclass
class Match:
    """Match data model."""

    id: int
    match_number: int
    home_team_id: Optional[int]
    away_team_id: Optional[int]
    home_team_name: Optional[str]
    away_team_name: Optional[str]
    city: str
    venue: str
    stage_id: int
    kickoff: str
    label: str
    api_football_fixture_id: Optional[int] = None


class FirestoreManager:
    """Manages tournament data in Firestore with smart caching."""

    def __init__(self):
        """Initialize Firestore client."""
        try:
            self.db = firestore.Client(project=config.FIRESTORE_PROJECT_ID)
        except Exception as e:
            logger.error(f"Failed to initialize Firestore: {e}")
            raise

        self.teams_collection = self.db.collection("teams")
        self.matches_collection = self.db.collection("matches")
        self.cities_collection = self.db.collection("host_cities")
        self.raw_api_responses_collection = self.db.collection("raw_api_responses")

    # ============================================================
    # TEAMS
    # ============================================================

    def get_team(self, team_id: int) -> Optional[Dict[str, Any]]:
        """
        Get team by ID.

        Args:
            team_id: Team ID

        Returns:
            Team dict or None if not found
        """
        doc = self.teams_collection.document(str(team_id)).get()

        if doc.exists:
            return doc.to_dict()

        return None

    def get_all_teams(self) -> List[Dict[str, Any]]:
        """
        Get all teams.

        Backward-compatible: Handles documents with/without sync metadata fields.

        Returns:
            List of team dicts
        """
        teams = []

        for doc in self.teams_collection.stream():
            team_data = doc.to_dict()

            # Ensure backward compatibility: add default values for missing sync fields
            if "api_football_raw_id" not in team_data:
                team_data["api_football_raw_id"] = None
            if "last_synced_at" not in team_data:
                team_data["last_synced_at"] = None
            if "manual_override" not in team_data:
                team_data["manual_override"] = False
            if "sync_conflicts" not in team_data:
                team_data["sync_conflicts"] = []

            teams.append(team_data)

        # Sort by ID
        teams.sort(key=lambda t: t.get("id", 0))

        return teams

    def get_teams_by_group(self, group_letter: str) -> List[Dict[str, Any]]:
        """
        Get all teams in a group.

        Args:
            group_letter: Group letter (A-L)

        Returns:
            List of team dicts
        """
        teams = []

        query = self.teams_collection.where("group", "==", group_letter)

        for doc in query.stream():
            teams.append(doc.to_dict())

        return teams

    def create_team(self, team: Team) -> None:
        """
        Create a new team.

        Args:
            team: Team dataclass
        """
        self.teams_collection.document(str(team.id)).set(
            {
                "id": team.id,
                "name": team.name,
                "fifa_code": team.fifa_code,
                "group": team.group,
                "api_football_id": team.api_football_id,
                "is_placeholder": team.is_placeholder,
                "stats": None,  # Will be populated on first API call
                # Sync metadata fields (backward-compatible)
                "api_football_raw_id": None,  # Reference to raw collection document
                "last_synced_at": None,  # ISO8601 timestamp
                "manual_override": False,  # Manual override flag
                "sync_conflicts": [],  # List of sync conflicts
            }
        )

        logger.info(f"Created team: {team.name} (ID: {team.id})")

    def update_team_stats(
        self, team_id: int, stats: Dict[str, Any], ttl_hours: int = 24
    ) -> None:
        """
        Update team stats with cache metadata.

        Args:
            team_id: Team ID
            stats: Stats dict from API-Football
            ttl_hours: Cache TTL in hours (default: 24)
        """
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=ttl_hours)

        self.teams_collection.document(str(team_id)).set(
            {
                "stats": {
                    **stats,
                    "fetched_at": now,
                    "expires_at": expires_at,
                }
            },
            merge=True,
        )

        logger.info(f"Updated stats for team {team_id} (expires: {expires_at})")

    def get_team_stats(self, team_id: int) -> Optional[Dict[str, Any]]:
        """
        Get team stats with cache check.

        Args:
            team_id: Team ID

        Returns:
            Stats dict or None if not cached or expired
        """
        team = self.get_team(team_id)

        if not team:
            return None

        stats = team.get("stats")

        if not stats:
            return None

        # Check if cache is fresh
        expires_at = stats.get("expires_at")

        if expires_at and self.is_cache_fresh(expires_at):
            logger.info(f"✅ Cache HIT for team {team_id}")
            return stats

        logger.info(f"❌ Cache EXPIRED for team {team_id}")
        return None

    # ============================================================
    # MATCHES
    # ============================================================

    def get_match(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        Get match by ID.

        Args:
            match_id: Match ID

        Returns:
            Match dict or None if not found
        """
        doc = self.matches_collection.document(str(match_id)).get()

        if doc.exists:
            return doc.to_dict()

        return None

    def get_all_matches(self) -> List[Dict[str, Any]]:
        """
        Get all matches.

        Backward-compatible: Handles documents with/without sync metadata fields.

        Returns:
            List of match dicts sorted by match_number
        """
        matches = []

        for doc in self.matches_collection.stream():
            match_data = doc.to_dict()

            # Ensure backward compatibility: add default values for missing sync fields
            if "api_football_raw_id" not in match_data:
                match_data["api_football_raw_id"] = None
            if "last_synced_at" not in match_data:
                match_data["last_synced_at"] = None
            if "manual_override" not in match_data:
                match_data["manual_override"] = False
            if "sync_conflicts" not in match_data:
                match_data["sync_conflicts"] = []

            matches.append(match_data)

        # Sort by match number
        matches.sort(key=lambda m: m.get("match_number", 0))

        return matches

    def get_matches_by_stage(self, stage_id: int) -> List[Dict[str, Any]]:
        """
        Get matches by stage.

        Args:
            stage_id: Stage ID (1=group, 2=ro32, etc.)

        Returns:
            List of match dicts
        """
        matches = []

        query = self.matches_collection.where("stage_id", "==", stage_id)

        for doc in query.stream():
            matches.append(doc.to_dict())

        # Sort by match number
        matches.sort(key=lambda m: m.get("match_number", 0))

        return matches

    def create_match(self, match: Match) -> None:
        """
        Create a new match.

        Args:
            match: Match dataclass
        """
        self.matches_collection.document(str(match.id)).set(
            {
                "id": match.id,
                "match_number": match.match_number,
                "home_team_id": match.home_team_id,
                "away_team_id": match.away_team_id,
                "home_team_name": match.home_team_name,
                "away_team_name": match.away_team_name,
                "city": match.city,
                "venue": match.venue,
                "stage_id": match.stage_id,
                "kickoff": match.kickoff,
                "label": match.label,
                "api_football_fixture_id": match.api_football_fixture_id,
                "prediction": None,  # Will be generated
                "has_real_data": False,
                # Sync metadata fields (backward-compatible)
                "api_football_raw_id": None,  # Reference to raw collection document
                "last_synced_at": None,  # ISO8601 timestamp
                "manual_override": False,  # Manual override flag
                "sync_conflicts": [],  # List of sync conflicts
            }
        )

        logger.info(f"Created match: {match.match_number}")

    def update_match_prediction(
        self, match_id: int, prediction: Dict[str, Any], team_stats_hash: str
    ) -> None:
        """
        Update match prediction with cache metadata.

        Args:
            match_id: Match ID
            prediction: Prediction dict from Gemini
            team_stats_hash: Hash of team stats used for prediction
        """
        now = datetime.utcnow()

        self.matches_collection.document(str(match_id)).set(
            {
                "prediction": {
                    **prediction,
                    "generated_at": now,
                    "team_stats_hash": team_stats_hash,
                }
            },
            merge=True,
        )

        logger.info(f"Updated prediction for match {match_id}")

    def get_match_prediction(self, match_id: int) -> Optional[Dict[str, Any]]:
        """
        Get match prediction.

        Args:
            match_id: Match ID

        Returns:
            Prediction dict or None if not generated
        """
        match = self.get_match(match_id)

        if not match:
            return None

        return match.get("prediction")

    def should_regenerate_prediction(
        self, match_id: int, current_stats_hash: str
    ) -> bool:
        """
        Check if prediction should be regenerated based on team stats changes.

        Args:
            match_id: Match ID
            current_stats_hash: Hash of current team stats

        Returns:
            True if prediction should be regenerated
        """
        prediction = self.get_match_prediction(match_id)

        if not prediction:
            # No prediction exists
            return True

        cached_hash = prediction.get("team_stats_hash")

        if not cached_hash:
            # No hash stored (old prediction format)
            return True

        if cached_hash != current_stats_hash:
            logger.info(f"Stats changed for match {match_id}, regenerating prediction")
            return True

        logger.info(f"Stats unchanged for match {match_id}, using cached prediction")
        return False

    # ============================================================
    # HOST CITIES
    # ============================================================

    def get_city(self, city_id: int) -> Optional[Dict[str, Any]]:
        """Get city by ID."""
        doc = self.cities_collection.document(str(city_id)).get()

        if doc.exists:
            return doc.to_dict()

        return None

    def create_city(
        self,
        city_id: int,
        city_name: str,
        country: str,
        venue_name: str,
        region_cluster: Optional[str] = None,
        airport_code: Optional[str] = None,
    ) -> None:
        """Create a new host city."""
        self.cities_collection.document(str(city_id)).set(
            {
                "id": city_id,
                "city_name": city_name,
                "country": country,
                "venue_name": venue_name,
                "region_cluster": region_cluster,
                "airport_code": airport_code,
            }
        )

        logger.info(f"Created city: {city_name} ({venue_name})")

    # ============================================================
    # RAW API RESPONSES (for API-Football sync)
    # ============================================================

    @property
    def api_football_raw_collection(self):
        """
        Get reference to raw API responses collection.

        Returns:
            Collection reference
        """
        return self.raw_api_responses_collection

    def store_raw_api_response(
        self,
        entity_type: str,
        league_id: int,
        season: int,
        raw_response: Dict[str, Any],
    ) -> str:
        """
        Store raw API-Football response in Firestore.

        Args:
            entity_type: Type of entity (teams, fixtures, etc.)
            league_id: League ID
            season: Season year
            raw_response: Raw API response dictionary

        Returns:
            Document ID of stored response
        """
        # Create document ID: "{entity_type}_{league_id}_{season}"
        document_id = f"{entity_type}_{league_id}_{season}"

        # Build document data
        document_data = {
            "entity_type": entity_type,
            "league_id": league_id,
            "season": season,
            "raw_response": raw_response,
            "fetched_at": datetime.utcnow(),
            "api_version": "v3",
            "endpoint": f"/teams" if entity_type == "teams" else f"/fixtures",
        }

        # Store in Firestore
        self.raw_api_responses_collection.document(document_id).set(document_data)

        logger.info(
            f"Stored raw API response: {document_id} (entity_type={entity_type}, league_id={league_id}, season={season})"
        )

        return document_id

    def get_raw_api_response(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve raw API-Football response from Firestore by document ID.

        Args:
            document_id: Document ID (format: "{entity_type}_{league_id}_{season}")

        Returns:
            Raw API response document or None if not found
        """
        # Fetch from Firestore
        doc = self.raw_api_responses_collection.document(document_id).get()

        if doc.exists:
            logger.info(f"Retrieved raw API response: {document_id}")
            return doc.to_dict()

        logger.info(f"Raw API response not found: {document_id}")
        return None

    # ============================================================
    # CACHE HELPERS
    # ============================================================

    @staticmethod
    def is_cache_fresh(expires_at: datetime) -> bool:
        """
        Check if cache is still valid.

        Args:
            expires_at: Expiration datetime

        Returns:
            True if cache is fresh
        """
        # Handle both timezone-aware and timezone-naive datetimes
        now = datetime.utcnow()

        # If expires_at is timezone-aware, make now timezone-aware too
        if expires_at.tzinfo is not None:
            from datetime import timezone

            now = datetime.now(timezone.utc)

        return expires_at > now

    @staticmethod
    def calculate_stats_hash(*stats_dicts: Dict[str, Any]) -> str:
        """
        Calculate hash of team stats for change detection.

        Only includes fields that affect predictions:
        - form_string
        - clean_sheets
        - avg_xg

        Args:
            *stats_dicts: Variable number of stats dicts

        Returns:
            MD5 hash of stats
        """
        # Extract only prediction-relevant fields
        relevant_data = []

        for stats in stats_dicts:
            if not stats:
                continue

            relevant = {
                "form_string": stats.get("form_string"),
                "clean_sheets": stats.get("clean_sheets"),
                "avg_xg": stats.get("avg_xg"),
            }
            relevant_data.append(str(sorted(relevant.items())))

        # Create hash
        combined = "|".join(relevant_data)
        return hashlib.md5(combined.encode()).hexdigest()
