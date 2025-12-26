"""
FastAPI main application for World Cup 2026 predictions.

Implements:
- POST /api/update-predictions: Full prediction pipeline
- GET /health: System health check
- CORS middleware for frontend integration
"""

import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from src.ai_agent import AIAgent
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
from src.firestore_publisher import FirestorePublisher

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s",
)

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
        try:
            fs_manager = FirestoreManager()
            teams = fs_manager.get_all_teams()
            firestore_status = "ok" if len(teams) > 0 else "error"
            logger.info(
                f"Firestore check: {firestore_status} ({len(teams)} teams loaded)"
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
            "teams_count": len(teams) if firestore_status == "ok" else 0,
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
        from src.db_manager import Team as TeamDataclass

        teams = [
            TeamDataclass(
                id=t["id"],
                name=t["name"],
                fifa_code=t["fifa_code"],
                group_letter=t[
                    "group"
                ],  # Firestore uses 'group', DBManager uses 'group_letter'
                is_placeholder=t.get("is_placeholder", False),
                api_football_id=t.get("api_football_id"),
            )
            for t in teams_data
        ]

        # Get matches from Firestore
        matches_data = fs_manager.get_all_matches()

        # Convert to Match dataclass for compatibility
        from src.db_manager import Match as MatchDataclass

        all_matches = [
            MatchDataclass(
                id=m["id"],
                match_number=m["match_number"],
                home_team_id=m.get("home_team_id"),
                away_team_id=m.get("away_team_id"),
                venue=m["venue"],
                stage_id=m["stage_id"],
                kickoff_at=m[
                    "kickoff"
                ],  # Firestore uses 'kickoff', DBManager uses 'kickoff_at'
                match_label=m[
                    "label"
                ],  # Firestore uses 'label', DBManager uses 'match_label'
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
        from src.db_manager import Team as TeamDataclass

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
        from src.db_manager import Match as MatchDataclass

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

                    if has_api_football_id:
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
            # Get existing snapshot
            doc_ref = publisher.db.collection("predictions").document("latest")
            doc_snap = doc_ref.get()

            if doc_snap.exists:
                snapshot = doc_snap.to_dict()
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

                # Debug: Log prediction structure
                logger.info(f"Total predictions: {len(predictions)}")
                if predictions:
                    sample_pred = predictions[0]
                    logger.info(f"Sample prediction keys: {list(sample_pred.keys())}")
                    logger.info(f"Sample prediction: {sample_pred}")

                # Extract group stage predictions (stage_id = 1)
                group_predictions = [p for p in predictions if p.get("stage_id") == 1]
                logger.info(
                    f"Group stage predictions (stage_id=1): {len(group_predictions)}"
                )

                # Calculate team win probabilities across all group matches
                team_win_prob = {}
                for pred in group_predictions:
                    # Find the team names from matches
                    match_id = pred.get("match_id")
                    match_data = next(
                        (
                            m
                            for m in snapshot.get("matches", [])
                            if m.get("id") == match_id
                        ),
                        None,
                    )

                    if match_data:
                        winner = pred.get("winner", "")
                        win_prob = pred.get("win_probability", 0.5)

                        # Add win probability to the winner
                        if winner and winner != "Draw":
                            if winner not in team_win_prob:
                                team_win_prob[winner] = {"total_prob": 0, "count": 0}
                            team_win_prob[winner]["total_prob"] += win_prob
                            team_win_prob[winner]["count"] += 1

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
        doc_ref = publisher.db.collection("predictions").document("latest")
        doc_snap = doc_ref.get()

        if not doc_snap.exists:
            raise HTTPException(
                status_code=404,
                detail="No predictions found. Run /api/update-predictions first.",
            )

        snapshot = doc_snap.to_dict()
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
