"""
FastAPI main application for World Cup 2026 predictions.

Implements:
- POST /api/update-predictions: Full prediction pipeline
- GET /health: System health check
- CORS middleware for frontend integration
"""

import logging
import uuid
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.ai_agent import AIAgent
from src.api_football_sync import APIFootballSync
from src.config import config
from src.data_aggregator import DataAggregator
from src.firestore_manager import FirestoreManager
from src.exceptions import (
    APIRateLimitError,
    DataAggregationError,
    FirestoreOperationError,
    GeminiFailureError,
)
from src.fifa_engine import FifaEngine
from src.fifa_ranking_scraper import FIFARankingScraper  # type: ignore[import-not-found]
from src.firestore_publisher import FirestorePublisher

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
)


# Pydantic models for request validation
class SyncRequest(BaseModel):
    """Request model for API-Football sync endpoint."""

    entity_type: str
    league_id: int
    season: int
    force_update: bool = False


class SyncFIFARankingsRequest(BaseModel):
    """Request model for FIFA rankings sync endpoint."""

    force_refresh: bool = False


# Initialize FastAPI application
app = FastAPI(
    title="World Cup 2026 Predictions API",
    description="AI-powered predictions for FIFA World Cup 2026",
    version="1.0.1",
)

# Configure CORS middleware (allow all origins in development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware for tracking
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID to all requests for logging/debugging."""
    request_id = str(uuid.uuid4())[:8]
    request.state.request_id = request_id

    # Add request_id to logging context
    logger_adapter = logging.LoggerAdapter(logger, {"request_id": request_id})
    logger_adapter.info(f"Request started: {request.method} {request.url.path}")

    response = await call_next(request)

    logger_adapter.info(f"Request completed: {response.status_code}")
    return response


@app.get("/health")
def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.

    Verifies:
    - Database connectivity
    - Firestore connectivity
    - Cache availability

    Returns:
        Health status dictionary with component statuses
    """
    logger.info("Health check requested")

    try:
        # Check Firestore connection (now our primary database)
        teams_count = 0
        try:
            fs_manager = FirestoreManager()
            teams = fs_manager.get_all_teams()
            teams_count = len(teams)
            firestore_status = "ok" if teams_count > 0 else "error"
            logger.info(
                f"Firestore check: {firestore_status} ({teams_count} teams loaded)"
            )
        except Exception as e:
            firestore_status = "error"
            logger.error(f"Firestore check failed: {e}")

        # Check cache size (file-based cache still used for API-Football responses)
        cache_dir = Path("backend/cache")
        cache_size = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0
        logger.info(f"Cache check: {cache_size} files")

        status = "healthy" if firestore_status == "ok" else "degraded"
        logger.info(f"Health check result: {status}")

        return {
            "status": status,
            "firestore": firestore_status,
            "teams_count": teams_count,
            "cache_size": cache_size,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.post("/api/update-tournament")
def update_tournament() -> Dict[str, Any]:
    """
    Load and publish tournament structure (groups, teams, matches).

    Pipeline:
    1. Load tournament structure from database
    2. Calculate group standings (using fifa_engine)
    3. Resolve knockout bracket with qualified teams
    4. Publish snapshot to Firestore (WITHOUT AI predictions)

    Returns:
        Status dictionary with timestamp

    Raises:
        HTTPException: 500 on any pipeline failures
    """
    logger.info("Tournament update pipeline started")
    pipeline_start = datetime.utcnow()

    try:
        errors: List[str] = []
        updated_at = pipeline_start.isoformat()

        # Step 1: Load tournament data from Firestore
        logger.info("Step 1: Loading tournament data from Firestore")
        fs_manager = FirestoreManager()

        # Get teams from Firestore (returns list of dicts)
        teams_data = fs_manager.get_all_teams()

        # Convert to Team dataclass for compatibility with existing code
        from src.types import Team as TeamDataclass

        teams = [
            TeamDataclass(
                id=t["id"],
                name=t["name"],
                fifa_code=t["fifa_code"],
                group_letter=t["group"],
                is_placeholder=t.get("is_placeholder", False),
                api_football_id=t.get("api_football_id"),
            )
            for t in teams_data
        ]

        # Get matches from Firestore
        matches_data = fs_manager.get_all_matches()

        # Convert to Match dataclass for compatibility
        from src.types import Match as MatchDataclass

        all_matches = [
            MatchDataclass(
                id=m["id"],
                match_number=m["match_number"],
                home_team_id=m.get("home_team_id"),
                away_team_id=m.get("away_team_id"),
                venue=m["venue"],
                stage_id=m["stage_id"],
                kickoff_at=m["kickoff"],
                match_label=m["label"],
            )
            for m in matches_data
        ]

        # Get knockout matches (stage_id >= 2)
        knockout_matches = [m for m in all_matches if m.stage_id >= 2]

        logger.info(
            f"Loaded {len(teams)} teams, {len(all_matches)} matches, {len(knockout_matches)} knockout matches from Firestore"
        )

        # Step 2: Calculate group standings
        logger.info("Step 2: Calculating group standings")
        engine = FifaEngine()

        # Group teams by group letter (include placeholders)
        groups: Dict[str, List[Any]] = {}
        for team in teams:
            if team.group_letter:
                if team.group_letter not in groups:
                    groups[team.group_letter] = []
                groups[team.group_letter].append(team)

        logger.info(f"Found {len(groups)} groups")

        # Calculate standings for each group
        # Initialize with empty results (pre-tournament state - 0 matches played)
        all_standings: Dict[str, Any] = {}
        for group_letter, group_teams in groups.items():
            try:
                # Initialize standings with team names only (no matches played)
                standings = engine.initialize_group_standings(
                    group_letter, [team.name for team in group_teams]
                )
                all_standings[group_letter] = standings
                logger.debug(
                    f"Initialized standings for Group {group_letter} with {len(standings)} teams"
                )
            except Exception as e:
                error_msg = (
                    f"Failed to calculate standings for Group {group_letter}: {str(e)}"
                )
                errors.append(error_msg)
                logger.error(error_msg)

        # Step 3: Rank third-place teams for knockout qualification
        try:
            third_place_qualifiers = engine.rank_third_place_teams(all_standings)
        except Exception as e:
            errors.append(f"Failed to rank third-place teams: {str(e)}")
            third_place_qualifiers = []

        # Step 4: Build bracket array (include ALL knockout matches, resolved or not)
        # Note: Resolution happens here, but we keep TBD for unresolved teams
        try:
            # Build knockout match data structure
            from dataclasses import dataclass

            @dataclass
            class KnockoutMatch:
                match_number: int
                home_team_label: str
                away_team_label: str
                venue: str
                kickoff_at: str
                stage_id: int

            knockout_match_data = []
            knockout_match_labels = {}  # Store original labels for TBD teams

            logger.info(f"Processing {len(knockout_matches)} knockout matches")

            for ko_match in knockout_matches:
                # Store original match label for later use
                knockout_match_labels[ko_match.match_number] = ko_match.match_label

                # Parse match_label to extract team labels
                if ko_match.match_label and " vs " in ko_match.match_label:
                    parts = ko_match.match_label.split(" vs ")
                    home_label = parts[0].strip()
                    away_label = parts[1].strip()

                    knockout_match_data.append(
                        KnockoutMatch(
                            match_number=ko_match.match_number,
                            home_team_label=home_label,
                            away_team_label=away_label,
                            venue=ko_match.venue,
                            kickoff_at=ko_match.kickoff_at,
                            stage_id=ko_match.stage_id,
                        )
                    )
                else:
                    logger.warning(
                        f"Match {ko_match.match_number} has invalid label: {ko_match.match_label}"
                    )

            logger.info(f"Built {len(knockout_match_data)} knockout match objects")

            # Resolve bracket (determine actual teams from labels)
            resolved_bracket = engine.resolve_knockout_bracket(
                all_standings, third_place_qualifiers, knockout_match_data
            )

            logger.info(f"Resolved {len(resolved_bracket)} bracket matches")

        except Exception as e:
            error_msg = f"Failed to resolve knockout bracket: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
            resolved_bracket = []

        # Step 5: Build tournament snapshot WITHOUT AI predictions
        # Extract favorites (top teams by points across all groups)
        all_teams_with_points = []
        for group_letter, standings in all_standings.items():
            for standing in standings:
                all_teams_with_points.append((standing.team_name, standing.points))

        # Sort by points and take top 5 as favorites
        all_teams_with_points.sort(key=lambda x: x[1], reverse=True)
        favorites = [team for team, points in all_teams_with_points[:5]]

        # Dark horses: 3rd place teams with good stats (could make a run)
        dark_horses = [standing.team_name for standing in third_place_qualifiers[:3]]

        # Build ALL matches (group stage + knockout)
        all_matches_data = []
        for match in all_matches:
            # Find team names (may be None for TBD knockout matches)
            home_team = (
                next((t for t in teams if t.id == match.home_team_id), None)
                if match.home_team_id
                else None
            )
            away_team = (
                next((t for t in teams if t.id == match.away_team_id), None)
                if match.away_team_id
                else None
            )

            # Use team names if available, otherwise use match label for TBD
            home_team_name = home_team.name if home_team else "TBD"
            away_team_name = away_team.name if away_team else "TBD"

            # Use match_label for TBD matches (e.g., "Winner A vs 3rd Place C/D/E")
            if match.match_label and (
                home_team_name == "TBD" or away_team_name == "TBD"
            ):
                label = match.match_label
            else:
                label = f"{home_team_name} vs {away_team_name}"

            all_matches_data.append(
                {
                    "id": match.id,
                    "match_number": match.match_number,
                    "stage_id": match.stage_id,
                    "home_team_id": match.home_team_id,
                    "away_team_id": match.away_team_id,
                    "home_team_name": home_team_name,
                    "away_team_name": away_team_name,
                    "venue": match.venue,
                    "kickoff": match.kickoff_at,
                    "label": label,
                }
            )

        # Add has_real_data flag to group standings
        snapshot = {
            "groups": {
                group: [
                    {
                        "team_name": standing.team_name,
                        "rank": standing.rank,
                        "points": standing.points,
                        "played": standing.played,
                        "won": standing.won,
                        "draw": standing.draw,
                        "lost": standing.lost,
                        "goals_for": standing.goals_for,
                        "goals_against": standing.goals_against,
                        "goal_difference": standing.goal_difference,
                        "has_real_data": False,  # Tournament structure doesn't have real match data yet
                    }
                    for standing in standings
                ]
                for group, standings in all_standings.items()
            },
            "matches": all_matches_data,
            "bracket": [
                {
                    "id": match.match_number,
                    "match_number": match.match_number,
                    "stage_id": match.stage_id,
                    "home_team_name": match.home_team_name,
                    "away_team_name": match.away_team_name,
                    "venue": match.venue,
                    "kickoff": match.kickoff_at,
                    # Use original labels if teams are TBD, otherwise use resolved team names
                    "label": (
                        f"{match.home_team_label} vs {match.away_team_label}"
                        if match.home_team_name == "TBD"
                        or match.away_team_name == "TBD"
                        else f"{match.home_team_name} vs {match.away_team_name}"
                    ),
                }
                for match in resolved_bracket
            ],
            "ai_summary": f"Turneringsstruktur lastet med {len(all_standings)} grupper, {len(all_matches_data)} kamper totalt ({len([m for m in all_matches_data if m['stage_id'] == 1])} gruppespill, {len([m for m in all_matches_data if m['stage_id'] > 1])} sluttspill)",
            "favorites": favorites,
            "darkHorses": dark_horses,
            "errors": errors if errors else None,
        }

        # Step 6: Publish to Firestore
        logger.info("Step 6: Publishing to Firestore")
        try:
            publisher = FirestorePublisher()
            publisher.publish_snapshot(snapshot)
            logger.info("Successfully published tournament snapshot to Firestore")
        except Exception as e:
            error_msg = f"Failed to publish to Firestore: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)

        elapsed = (datetime.utcnow() - pipeline_start).total_seconds()
        status = "success" if not errors else "partial_success"
        logger.info(
            f"Tournament update pipeline {status} (elapsed {elapsed:.2f}s, {len(errors)} errors)"
        )

        return {
            "status": status,
            "updated_at": updated_at,
            "groups_calculated": len(all_standings),
            "bracket_matches_resolved": len(resolved_bracket),
            "elapsed_seconds": round(elapsed, 2),
            "errors": errors if errors else None,
        }

    except Exception as e:
        # Top-level error handling
        elapsed = (datetime.utcnow() - pipeline_start).total_seconds()
        logger.error(f"Tournament update pipeline FAILED (elapsed {elapsed:.2f}s): {e}")
        raise HTTPException(
            status_code=500, detail=f"Tournament update failed: {str(e)}"
        )


@app.post("/api/update-predictions")
def update_predictions() -> Dict[str, Any]:
    """
    Generate and publish AI predictions for matches.

    This is a separate step from loading tournament structure.
    Run /api/update-tournament first to load teams and matches.

    Pipeline:
    1. Fetch existing tournament data from Firestore
    2. Fetch team statistics (with caching via data_aggregator)
    3. Generate AI predictions for all matches
    4. Update Firestore with predictions

    Returns:
        Status dictionary with predictions count and timestamp

    Raises:
        HTTPException: 500 on any pipeline failures
    """
    logger.info("Predictions update pipeline started")
    pipeline_start = datetime.utcnow()

    try:
        errors: List[str] = []
        warnings: List[str] = []
        updated_at = pipeline_start.isoformat()

        # Step 1: Load tournament data from Firestore
        logger.info("Step 1: Loading tournament data from Firestore")
        fs_manager = FirestoreManager()

        # Get teams from Firestore
        teams_data = fs_manager.get_all_teams()

        # Convert to Team dataclass for compatibility
        from src.types import Team as TeamDataclass

        teams = [
            TeamDataclass(
                id=t["id"],
                name=t["name"],
                fifa_code=t["fifa_code"],
                group_letter=t["group"],
                is_placeholder=t.get("is_placeholder", False),
                api_football_id=t.get("api_football_id"),
            )
            for t in teams_data
        ]

        # Get matches from Firestore
        matches_data = fs_manager.get_all_matches()

        # Convert to Match dataclass for compatibility
        from src.types import Match as MatchDataclass

        all_matches = [
            MatchDataclass(
                id=m["id"],
                match_number=m["match_number"],
                home_team_id=m.get("home_team_id"),
                away_team_id=m.get("away_team_id"),
                venue=m["venue"],
                stage_id=m["stage_id"],
                kickoff_at=m["kickoff"],
                match_label=m["label"],
            )
            for m in matches_data
        ]

        logger.info(
            f"Loaded {len(teams)} teams, {len(all_matches)} matches from Firestore"
        )

        # Step 2: Fetch team statistics with smart caching (Firestore)
        logger.info("Step 2: Fetching team statistics with smart caching")
        aggregator = DataAggregator()
        team_stats: Dict[int, Dict[str, Any]] = {}
        firestore_cache_hits = 0
        firestore_cache_misses = 0

        for team in teams:
            if team.is_placeholder:
                continue

            # Check if team has API-Football ID (indicates real data availability)
            has_api_football_id = team.api_football_id is not None

            try:
                # Try Firestore cache first (24-hour TTL)
                cached_stats = fs_manager.get_team_stats(team.id)

                if cached_stats:
                    # Cache HIT - use cached stats
                    team_stats[team.id] = cached_stats
                    team_stats[team.id]["has_real_data"] = has_api_football_id
                    firestore_cache_hits += 1
                else:
                    # Cache MISS - fetch from API-Football
                    firestore_cache_misses += 1

                    if has_api_football_id and team.api_football_id is not None:
                        # Fetch real data from API-Football (with xG enabled)
                        stats = aggregator.fetch_team_stats(
                            team.api_football_id, fetch_xg=True
                        )
                        stats["has_real_data"] = True
                        team_stats[team.id] = stats

                        # Update Firestore cache (24-hour TTL)
                        fs_manager.update_team_stats(team.id, stats, ttl_hours=24)
                    else:
                        # Use fallback stats for teams without API-Football ID
                        fallback_stats = {
                            "avg_xg": None,
                            "clean_sheets": 0,
                            "form_string": "Unknown",
                            "confidence": "low",
                            "has_real_data": False,
                        }
                        team_stats[team.id] = fallback_stats

                        # Cache fallback stats too (shorter TTL)
                        fs_manager.update_team_stats(
                            team.id, fallback_stats, ttl_hours=6
                        )

            except (APIRateLimitError, DataAggregationError) as e:
                error_msg = f"Failed to fetch stats for {team.name}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
                # Fallback to mock data
                team_stats[team.id] = {
                    "avg_xg": None,
                    "clean_sheets": 0,
                    "form_string": "Unknown",
                    "confidence": "low",
                    "has_real_data": False,
                }
            except Exception as e:
                warning_msg = (
                    f"Unexpected error fetching stats for {team.name}: {str(e)}"
                )
                warnings.append(warning_msg)
                logger.warning(warning_msg)
                # Fallback to mock data
                team_stats[team.id] = {
                    "avg_xg": None,
                    "clean_sheets": 0,
                    "form_string": "Unknown",
                    "confidence": "low",
                    "has_real_data": False,
                }

        logger.info(
            f"Team stats: {firestore_cache_hits} Firestore cache hits, "
            f"{firestore_cache_misses} cache misses (API calls made)"
        )

        # Step 2.5: Enrich team stats with FIFA rankings
        logger.info("Step 2.5: Enriching team stats with FIFA rankings")
        fifa_scraper = FIFARankingScraper()
        fifa_enriched_count = 0
        fifa_missing_count = 0
        
        for team in teams:
            if team.is_placeholder:
                continue
            
            # Skip if no FIFA code available
            if not team.fifa_code:
                logger.debug(f"Team {team.name} has no FIFA code - skipping ranking lookup")
                fifa_missing_count += 1
                continue
            
            try:
                # Get FIFA ranking for this team
                ranking_data = fifa_scraper.get_ranking_for_team(team.fifa_code)
                
                if ranking_data:
                    # Add FIFA ranking fields to team stats
                    if team.id in team_stats:
                        team_stats[team.id]["fifa_ranking"] = ranking_data.get("rank")
                        team_stats[team.id]["fifa_points"] = ranking_data.get("points")
                        team_stats[team.id]["fifa_confederation"] = ranking_data.get("confederation")
                        fifa_enriched_count += 1
                        logger.debug(
                            f"Enriched {team.name} with FIFA ranking: #{ranking_data.get('rank')}"
                        )
                else:
                    # Ranking not found - log warning but continue
                    logger.warning(
                        f"FIFA ranking not found for {team.name} (code: {team.fifa_code})"
                    )
                    fifa_missing_count += 1
                    
            except Exception as e:
                # Graceful degradation - log warning but don't fail
                logger.warning(
                    f"Failed to get FIFA ranking for {team.name}: {e}"
                )
                fifa_missing_count += 1
        
        logger.info(
            f"FIFA ranking enrichment: {fifa_enriched_count} teams enriched, "
            f"{fifa_missing_count} teams missing ranking data"
        )

        # Step 3: Generate AI predictions for all matches (with smart caching)
        logger.info("Step 3: Generating AI predictions with smart caching")
        agent = AIAgent()
        predictions: List[Dict[str, Any]] = []
        gemini_success = 0
        gemini_fallback = 0
        predictions_cached = 0
        predictions_regenerated = 0

        for match in all_matches:
            # Skip matches with placeholder teams
            if match.home_team_id is None or match.away_team_id is None:
                continue

            try:
                # Find team names
                home_team = next((t for t in teams if t.id == match.home_team_id), None)
                away_team = next((t for t in teams if t.id == match.away_team_id), None)

                if not home_team or not away_team:
                    continue

                # Get team stats (with has_real_data flag)
                home_stats = team_stats.get(home_team.id, {})
                away_stats = team_stats.get(away_team.id, {})

                # Calculate hash of current team stats
                current_stats_hash = fs_manager.calculate_stats_hash(
                    home_stats, away_stats
                )

                # Check if we need to regenerate prediction
                should_regenerate = fs_manager.should_regenerate_prediction(
                    match.id, current_stats_hash
                )

                if not should_regenerate:
                    # Use cached prediction
                    cached_prediction = fs_manager.get_match_prediction(match.id)
                    if cached_prediction is not None:
                        predictions_cached += 1

                        # Add to predictions list
                        predictions.append(
                            {
                                "match_id": match.id,
                                "match_number": match.match_number,
                                "has_real_data": home_stats.get("has_real_data", False)
                                and away_stats.get("has_real_data", False),
                                **cached_prediction,
                            }
                        )
                        continue

                # Need to regenerate prediction
                predictions_regenerated += 1

                # Determine if match has real data (both teams must have real data)
                match_has_real_data = home_stats.get(
                    "has_real_data", False
                ) and away_stats.get("has_real_data", False)

                # Try to fetch API-Football prediction if we have a fixture_id
                api_football_prediction = None
                if (
                    hasattr(match, "api_football_fixture_id")
                    and match.api_football_fixture_id
                ):
                    try:
                        api_football_prediction = aggregator.fetch_match_prediction(
                            match.api_football_fixture_id
                        )
                        if api_football_prediction:
                            logger.info(
                                f"✅ API-Football prediction fetched for match {match.match_number}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Failed to fetch API-Football prediction for match {match.match_number}: {e}"
                        )

                # Build matchup data
                matchup = {
                    "match_id": match.id,
                    "match_number": match.match_number,
                    "stage_id": match.stage_id,
                    "home_team": {
                        "name": home_team.name,
                        **home_stats,
                    },
                    "away_team": {
                        "name": away_team.name,
                        **away_stats,
                    },
                    "api_football_prediction": api_football_prediction,
                }

                # Generate NEW prediction with Gemini
                prediction = agent.generate_prediction(matchup)

                # Save prediction to Firestore with stats hash
                fs_manager.update_match_prediction(
                    match.id, prediction, current_stats_hash
                )

                # Track if fallback was used
                if prediction.get("confidence") == "low":
                    gemini_fallback += 1
                else:
                    gemini_success += 1

                predictions.append(
                    {
                        "match_id": match.id,
                        "match_number": match.match_number,
                        "has_real_data": match_has_real_data,
                        **prediction,
                    }
                )

            except GeminiFailureError as e:
                error_msg = (
                    f"Gemini prediction failed for match {match.match_number}: {str(e)}"
                )
                errors.append(error_msg)
                logger.error(error_msg)
            except Exception as e:
                error_msg = f"Failed to predict match {match.match_number}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)

        logger.info(
            f"Predictions: {predictions_cached} cached (reused), "
            f"{predictions_regenerated} regenerated ({gemini_success} Gemini success, {gemini_fallback} fallback)"
        )

        # Step 4: Fetch existing tournament data from Firestore and update with predictions
        try:
            publisher = FirestorePublisher()
            if publisher.db is None:
                raise HTTPException(
                    status_code=500,
                    detail="Firestore client not initialized",
                )
            # Get existing snapshot
            doc_ref = publisher.db.collection("predictions").document("latest")
            doc_snap = doc_ref.get()

            if doc_snap.exists:  # type: ignore[union-attr]
                snapshot = doc_snap.to_dict()  # type: ignore[union-attr]
                if snapshot is None:
                    raise HTTPException(
                        status_code=500,
                        detail="Tournament snapshot exists but is empty. Run /api/update-tournament first.",
                    )
                # Add predictions to existing snapshot
                snapshot["predictions"] = predictions
                snapshot["ai_summary"] = (
                    f"Genererte {len(predictions)} AI-spådommer for VM 2026"
                )

                # Merge has_real_data flag from predictions into matches array
                if "matches" in snapshot and predictions:
                    # Create a map of match_id -> has_real_data
                    has_real_data_map = {
                        pred["match_id"]: pred.get("has_real_data", False)
                        for pred in predictions
                    }

                    # Update each match with has_real_data flag
                    for match in snapshot["matches"]:
                        match_id = match.get("id")
                        if match_id in has_real_data_map:
                            match["has_real_data"] = has_real_data_map[match_id]
                        else:
                            match["has_real_data"] = False

                # Recalculate favorites and dark horses based on AI predictions
                logger.info(
                    "Recalculating favorites and dark horses from AI predictions"
                )

                # Calculate team win probabilities across all group matches
                # Note: stage_id is in matches, not in predictions
                team_win_prob = {}
                group_stage_count = 0

                for pred in predictions:
                    # Find the match data to get stage_id
                    match_id = pred.get("match_id")
                    match_data = next(
                        (
                            m
                            for m in snapshot.get("matches", [])
                            if m.get("id") == match_id
                        ),
                        None,
                    )

                    # Only process group stage matches (stage_id = 1)
                    if match_data and match_data.get("stage_id") == 1:
                        group_stage_count += 1
                        winner = pred.get("winner", "")
                        win_prob = pred.get("win_probability", 0.5)

                        # Add win probability to the winner
                        if winner and winner != "Draw":
                            if winner not in team_win_prob:
                                team_win_prob[winner] = {"total_prob": 0, "count": 0}
                            team_win_prob[winner]["total_prob"] += win_prob
                            team_win_prob[winner]["count"] += 1

                logger.info(f"Processed {group_stage_count} group stage predictions")
                logger.info(f"Teams with win probabilities: {len(team_win_prob)}")

                # Calculate average win probability for each team
                team_avg_prob = {
                    team: data["total_prob"] / data["count"]
                    for team, data in team_win_prob.items()
                    if data["count"] > 0
                }

                # Sort by average win probability and take top 5 as favorites
                sorted_teams = sorted(
                    team_avg_prob.items(), key=lambda x: x[1], reverse=True
                )
                favorites = [team for team, prob in sorted_teams[:5]]

                # Dark horses: Teams with moderate win probability (0.55-0.70 range) - potential underdogs
                dark_horse_candidates = [
                    (team, prob) for team, prob in sorted_teams if 0.55 <= prob <= 0.70
                ]
                dark_horses = [team for team, prob in dark_horse_candidates[:3]]

                # Update snapshot with new favorites and dark horses
                snapshot["favorites"] = favorites
                snapshot["darkHorses"] = dark_horses

                logger.info(f"Updated favorites: {favorites}")
                logger.info(f"Updated dark horses: {dark_horses}")

                # Calculate AI predicted standings for each group
                logger.info("Calculating AI predicted group standings")
                engine = FifaEngine()

                if "groups" in snapshot:
                    for group_letter, group_standings in snapshot["groups"].items():
                        # Get team names in this group
                        team_names = [s["team_name"] for s in group_standings]

                        # Get all group stage predictions for this group
                        group_predictions = []
                        for pred in predictions:
                            # Find the match data to get team names
                            match_id = pred.get("match_id")
                            match_data = next(
                                (
                                    m
                                    for m in snapshot.get("matches", [])
                                    if m.get("id") == match_id
                                    and m.get("stage_id") == 1
                                ),
                                None,
                            )

                            if match_data:
                                home_team = match_data.get("home_team_name")
                                away_team = match_data.get("away_team_name")

                                # Only include matches for this group
                                if home_team in team_names and away_team in team_names:
                                    group_predictions.append(
                                        {
                                            "home_team_name": home_team,
                                            "away_team_name": away_team,
                                            "predicted_home_score": pred.get(
                                                "predicted_home_score", 0
                                            ),
                                            "predicted_away_score": pred.get(
                                                "predicted_away_score", 0
                                            ),
                                        }
                                    )

                        # Calculate predicted rankings based on AI predictions
                        if group_predictions:
                            predicted_ranks = engine.calculate_predicted_standings(
                                group_letter=group_letter,
                                team_names=team_names,
                                group_predictions=group_predictions,
                            )

                            # Update each team in the group with predicted_rank
                            for team_standing in group_standings:
                                team_name = team_standing["team_name"]
                                if team_name in predicted_ranks:
                                    team_standing["predicted_rank"] = predicted_ranks[
                                        team_name
                                    ]
                                    logger.debug(
                                        f"Group {group_letter}: {team_name} predicted rank = {predicted_ranks[team_name]}"
                                    )

                            logger.info(
                                f"Group {group_letter}: Calculated predicted ranks for {len(predicted_ranks)} teams"
                            )
                        else:
                            logger.warning(
                                f"Group {group_letter}: No predictions found for ranking calculation"
                            )

            else:
                # No existing tournament data - need to run /api/update-tournament first
                raise HTTPException(
                    status_code=400,
                    detail="No tournament data found. Run /api/update-tournament first.",
                )
        except Exception as e:
            if isinstance(e, HTTPException):
                raise
            errors.append(f"Failed to load existing tournament data: {str(e)}")
            return {
                "status": "error",
                "errors": errors,
            }

        # Step 5: Publish updated snapshot to Firestore
        logger.info("Step 5: Publishing updated snapshot to Firestore")
        try:
            publisher.publish_snapshot(snapshot)
            logger.info("Successfully published predictions to Firestore")
        except Exception as e:
            error_msg = f"Failed to publish to Firestore: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg)
            raise FirestoreOperationError("publish_snapshot", str(e)) from e

        elapsed = (datetime.utcnow() - pipeline_start).total_seconds()
        status = "success" if not errors else "partial_success"
        logger.info(
            f"Predictions update pipeline {status} (elapsed {elapsed:.2f}s, {len(predictions)} predictions, {len(errors)} errors)"
        )

        return {
            "status": status,
            "updated_at": updated_at,
            "predictions_generated": len(predictions),
            "gemini_success": gemini_success,
            "gemini_fallback": gemini_fallback,
            "firestore_cache_hits": firestore_cache_hits,
            "firestore_cache_misses": firestore_cache_misses,
            "predictions_cached": predictions_cached,
            "predictions_regenerated": predictions_regenerated,
            "elapsed_seconds": round(elapsed, 2),
            "errors": errors if errors else None,
            "warnings": warnings if warnings else None,
        }

    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        # Top-level error handling
        elapsed = (datetime.utcnow() - pipeline_start).total_seconds()
        logger.error(
            f"Predictions update pipeline FAILED (elapsed {elapsed:.2f}s): {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Prediction pipeline failed: {str(e)}"
        )


@app.post("/api/sync-api-football")
def sync_api_football(request: SyncRequest) -> Dict[str, Any]:
    """
    Sync teams or fixtures from API-Football to Firestore.

    This endpoint handles synchronization of API-Football data including:
    - Storing raw API responses
    - Detecting changes between API and Firestore data
    - Resolving conflicts with manual overrides
    - Updating Firestore collections

    Args:
        request: SyncRequest with entity_type, league_id, season, and force_update

    Returns:
        SyncResult dictionary with sync statistics

    Raises:
        HTTPException: 400 for invalid entity_type, 500 for sync failures
    """
    logger.info(
        f"API-Football sync requested: entity_type={request.entity_type}, "
        f"league_id={request.league_id}, season={request.season}, "
        f"force_update={request.force_update}"
    )

    try:
        # Initialize dependencies
        firestore_manager = FirestoreManager()
        data_aggregator = DataAggregator()
        sync = APIFootballSync(firestore_manager, data_aggregator)

        # Route based on entity_type
        if request.entity_type == "teams":
            result = sync.sync_teams(
                league_id=request.league_id,
                season=request.season,
                force_update=request.force_update,
            )
        elif request.entity_type == "fixtures":
            result = sync.sync_fixtures(
                league_id=request.league_id,
                season=request.season,
                force_update=request.force_update,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid entity_type: {request.entity_type}. Must be 'teams' or 'fixtures'.",
            )

        # Convert SyncResult dataclass to dict for JSON response
        # Handle both dataclass and dict (for testing with mocks)
        if isinstance(result, dict):
            response_data = result
        else:
            response_data = asdict(result)
            # Remove empty errors list
            if response_data.get("errors") == []:
                response_data["errors"] = None

        # Log completion (handle both dict and dataclass)
        status = result.get("status") if isinstance(result, dict) else result.status
        changes = (
            result.get("changes_detected")
            if isinstance(result, dict)
            else result.changes_detected
        )
        logger.info(f"API-Football sync completed: {status}, {changes} changes")

        return response_data

    except HTTPException:
        # Re-raise HTTPException as-is
        raise
    except Exception as e:
        logger.error(f"API-Football sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"API-Football sync failed: {str(e)}"
        )


@app.post("/api/sync-match-flags")
async def sync_match_flags():
    """
    Sync has_real_data flags from predictions to matches array.

    This is a lightweight operation that doesn't regenerate predictions.
    Use this when you just need to update the matches array with flags
    from existing predictions (e.g., after fixing the data transformation).
    """
    try:
        logger.info("Syncing has_real_data flags from predictions to matches")

        # Get existing snapshot from Firestore
        publisher = FirestorePublisher()
        if publisher.db is None:
            raise HTTPException(
                status_code=500,
                detail="Firestore client not initialized",
            )
        doc_ref = publisher.db.collection("predictions").document("latest")
        doc_snap = doc_ref.get()

        if not doc_snap.exists:  # type: ignore[union-attr]
            raise HTTPException(
                status_code=404,
                detail="No predictions found. Run /api/update-predictions first.",
            )

        snapshot = doc_snap.to_dict()  # type: ignore[union-attr]
        if snapshot is None:
            raise HTTPException(
                status_code=500,
                detail="Snapshot is empty",
            )
        predictions = snapshot.get("predictions", [])

        if not predictions:
            raise HTTPException(
                status_code=400,
                detail="No predictions in snapshot. Run /api/update-predictions first.",
            )

        # Create has_real_data map from predictions
        has_real_data_map = {
            pred["match_id"]: pred.get("has_real_data", False) for pred in predictions
        }

        # Update matches array
        updated_count = 0
        if "matches" in snapshot:
            for match in snapshot["matches"]:
                match_id = match.get("id")
                if match_id in has_real_data_map:
                    match["has_real_data"] = has_real_data_map[match_id]
                    updated_count += 1
                else:
                    match["has_real_data"] = False

        # Publish updated snapshot
        publisher.publish_snapshot(snapshot)
        logger.info(f"Successfully synced {updated_count} match flags")

        return {
            "status": "success",
            "matches_updated": updated_count,
            "total_predictions": len(predictions),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to sync match flags: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to sync match flags: {str(e)}"
        )


@app.post("/api/sync-fifa-rankings")
def sync_fifa_rankings(request: SyncFIFARankingsRequest) -> Dict[str, Any]:
    """
    Manually trigger FIFA world rankings sync.

    This endpoint scrapes FIFA rankings from https://inside.fifa.com/fifa-world-ranking/men
    and stores them in Firestore with a 30-day TTL cache.

    Args:
        request: SyncFIFARankingsRequest with force_refresh option

    Returns:
        Dictionary with:
            - success: bool
            - teams_scraped: int
            - duration_seconds: float
            - fetched_at: datetime (ISO format string)
            - cache_expires_at: datetime (ISO format string)
            - error: str (only if failure)
            - cached_data_available: bool (only if failure)

    Raises:
        HTTPException: 500 on scraping failures
    """
    logger.info(f"FIFA rankings sync requested (force_refresh={request.force_refresh})")
    
    try:
        # Instantiate scraper and run scrape_and_store workflow
        scraper = FIFARankingScraper()
        result = scraper.scrape_and_store(force_refresh=request.force_refresh)
        
        # Build response
        if result.get('success'):
            response = {
                "success": True,
                "teams_scraped": result.get('teams_scraped', 0),
                "duration_seconds": result.get('duration_seconds', 0.0),
                "fetched_at": result.get('fetched_at').isoformat() if result.get('fetched_at') else None,
                "cache_expires_at": result.get('cache_expires_at').isoformat() if result.get('cache_expires_at') else None,
                "source_url": scraper.RANKINGS_URL,
            }
            
            if result.get('cache_hit'):
                response["cache_hit"] = True
            
            logger.info(
                f"FIFA rankings sync SUCCESS: {result.get('teams_scraped')} teams "
                f"in {result.get('duration_seconds'):.2f}s"
            )
            return response
        else:
            # Scraping failed - check if cached data is available
            cached_available = False
            try:
                fs_manager = FirestoreManager()
                cached_data = fs_manager.get_fifa_rankings()
                cached_available = cached_data is not None
            except Exception:
                pass
            
            error_msg = result.get('error_message', 'Unknown error')
            logger.error(f"FIFA rankings sync FAILED: {error_msg}")
            
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": error_msg,
                    "teams_scraped": 0,
                    "cached_data_available": cached_available,
                }
            )
    
    except HTTPException:
        raise
    except DataAggregationError as e:
        logger.error(f"FIFA rankings sync failed with DataAggregationError: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": f"Failed to scrape FIFA rankings: {str(e)}",
                "teams_scraped": 0,
                "cached_data_available": False,
            }
        )
    except Exception as e:
        logger.error(f"FIFA rankings sync failed with unexpected error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"FIFA rankings sync failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
