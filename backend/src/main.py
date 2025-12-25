"""
FastAPI main application for World Cup 2026 predictions.

Implements:
- POST /api/update-predictions: Full prediction pipeline
- GET /health: System health check
- CORS middleware for frontend integration
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.ai_agent import AIAgent
from src.config import config
from src.data_aggregator import DataAggregator
from src.db_manager import DBManager
from src.fifa_engine import FifaEngine
from src.firestore_publisher import FirestorePublisher

# Database path (relative to backend directory)
DB_PATH = Path(__file__).parent.parent / "worldcup2026.db"

# Initialize FastAPI application
app = FastAPI(
    title="World Cup 2026 Predictions API",
    description="AI-powered predictions for FIFA World Cup 2026",
    version="1.0.0",
)

# Configure CORS middleware (allow all origins in development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    try:
        # Check database connection
        db = DBManager(str(DB_PATH))
        teams = db.load_all_teams()
        db_status = "ok" if len(teams) > 0 else "error"

        # Check Firestore connection
        # Note: Full connection test would require actual Firestore read
        # For now, we verify the publisher initializes
        try:
            publisher = FirestorePublisher()
            firestore_status = "ok" if publisher.db is not None else "not_configured"
        except Exception:
            firestore_status = "error"

        # Check cache size
        cache_dir = Path("backend/cache")
        cache_size = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0

        return {
            "status": "healthy" if db_status == "ok" else "degraded",
            "database": db_status,
            "firestore": firestore_status,
            "cache_size": cache_size,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }


@app.post("/api/update-predictions")
def update_predictions() -> Dict[str, Any]:
    """
    Generate and publish tournament predictions.

    Pipeline:
    1. Load tournament structure from database
    2. Calculate group standings (using fifa_engine)
    3. Fetch team statistics (with caching via data_aggregator)
    4. Generate AI predictions for all matches
    5. Resolve knockout bracket with qualified teams
    6. Publish snapshot to Firestore

    Returns:
        Status dictionary with predictions count and timestamp

    Raises:
        HTTPException: 500 on any pipeline failures
    """
    try:
        errors: List[str] = []
        updated_at = datetime.utcnow().isoformat()

        # Step 1: Load tournament data from SQLite
        db = DBManager(str(DB_PATH))
        teams = db.load_all_teams()
        all_matches = db.load_all_matches()
        knockout_matches = db.load_knockout_matches()

        # Step 2: Calculate group standings
        # Note: This requires match results. Since we don't have actual results yet,
        # we'll use simulated/empty results for now.
        # In production, you'd load actual match results from a results table.
        engine = FifaEngine()

        # Group teams by group letter
        groups: Dict[str, List[Any]] = {}
        for team in teams:
            if team.group_letter and not team.is_placeholder:
                if team.group_letter not in groups:
                    groups[team.group_letter] = []
                groups[team.group_letter].append(team)

        # Calculate standings for each group
        # For now, using empty results (pre-tournament state)
        # TODO: Load actual match results when available
        all_standings: Dict[str, Any] = {}
        for group_letter, group_teams in groups.items():
            try:
                # Empty results = all teams with 0 points
                standings = engine.calculate_standings(group_letter, [])
                all_standings[group_letter] = standings
            except Exception as e:
                errors.append(
                    f"Failed to calculate standings for Group {group_letter}: {str(e)}"
                )

        # Step 3: Rank third-place teams for knockout qualification
        try:
            third_place_qualifiers = engine.rank_third_place_teams(all_standings)
        except Exception as e:
            errors.append(f"Failed to rank third-place teams: {str(e)}")
            third_place_qualifiers = []

        # Step 4: Fetch team statistics with caching
        aggregator = DataAggregator()
        team_stats: Dict[int, Dict[str, Any]] = {}

        for team in teams:
            if team.is_placeholder:
                continue

            try:
                # Try cache first
                cached = aggregator.get_cached_stats(team.id)
                if cached:
                    team_stats[team.id] = cached
                else:
                    # Cache miss - would fetch from API in production
                    # For now, use fallback stats
                    team_stats[team.id] = {
                        "avg_xg": None,
                        "clean_sheets": 0,
                        "form_string": "Unknown",
                        "confidence": "low",
                    }
                    # Save to cache
                    aggregator.save_to_cache(team.id, team_stats[team.id])
            except Exception as e:
                errors.append(f"Failed to fetch stats for {team.name}: {str(e)}")

        # Step 5: Generate AI predictions for all matches
        agent = AIAgent()
        predictions: List[Dict[str, Any]] = []

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

                # Build matchup data
                matchup = {
                    "match_id": match.id,
                    "match_number": match.match_number,
                    "stage_id": match.stage_id,
                    "home_team": {
                        "name": home_team.name,
                        **team_stats.get(home_team.id, {}),
                    },
                    "away_team": {
                        "name": away_team.name,
                        **team_stats.get(away_team.id, {}),
                    },
                }

                # Generate prediction
                prediction = agent.generate_prediction(matchup)
                predictions.append(
                    {
                        "match_id": match.id,
                        "match_number": match.match_number,
                        **prediction,
                    }
                )

            except Exception as e:
                errors.append(f"Failed to predict match {match.match_number}: {str(e)}")

        # Step 6: Resolve knockout bracket
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
            for ko_match in knockout_matches:
                # Parse match_label to extract team labels
                # Format: "Winner A vs Runner-up B" or "Team A vs 3rd Place C/D/E"
                if " vs " in ko_match.match_label:
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

            resolved_bracket = engine.resolve_knockout_bracket(
                all_standings, third_place_qualifiers, knockout_match_data
            )
        except Exception as e:
            errors.append(f"Failed to resolve knockout bracket: {str(e)}")
            resolved_bracket = []

        # Step 7: Build tournament snapshot
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
                    }
                    for standing in standings
                ]
                for group, standings in all_standings.items()
            },
            "bracket": [
                {
                    "match_number": match.match_number,
                    "stage_id": match.stage_id,
                    "home_team": match.home_team_name,
                    "away_team": match.away_team_name,
                    "venue": match.venue,
                    "kickoff_at": match.kickoff_at,
                }
                for match in resolved_bracket
            ],
            "predictions": predictions,
            "ai_summary": f"Generated {len(predictions)} predictions for World Cup 2026",
            "errors": errors if errors else None,
        }

        # Step 8: Publish to Firestore
        try:
            publisher = FirestorePublisher()
            publisher.publish_snapshot(snapshot)
        except Exception as e:
            errors.append(f"Failed to publish to Firestore: {str(e)}")
            # Continue execution - local snapshot is still valid

        return {
            "status": "success" if not errors else "partial_success",
            "updated_at": updated_at,
            "predictions_generated": len(predictions),
            "groups_calculated": len(all_standings),
            "bracket_matches_resolved": len(resolved_bracket),
            "errors": errors if errors else None,
        }

    except Exception as e:
        # Top-level error handling
        raise HTTPException(
            status_code=500, detail=f"Prediction pipeline failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
