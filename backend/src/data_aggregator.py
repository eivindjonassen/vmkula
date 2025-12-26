"""
Data aggregation module for fetching team statistics from API-Football.

Implements:
- Team metrics computation (xG, clean sheets, form)
- Missing data handling with fallback modes
- Local caching (24-hour TTL)
- Rate limiting (0.5s delay between requests)
- Exponential backoff retry logic
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

import requests

from src.config import config
from src.exceptions import APIRateLimitError, DataAggregationError

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


@dataclass
class TeamStatistics:
    """Team performance statistics."""

    avg_xg: Optional[float]
    clean_sheets: int
    form_string: str
    data_completeness: float
    confidence: str
    fallback_mode: Optional[str] = None


class DataAggregator:
    """Aggregates team statistics from API-Football with caching and rate limiting."""

    def __init__(self, cache_dir: str = "backend/cache"):
        """
        Initialize data aggregator.

        Args:
            cache_dir: Directory for local cache storage
        """
        self.cache_dir = cache_dir
        self.last_request_time = 0.0

    def transform_api_response(
        self, api_response: Dict[str, Any], team_id: int, fetch_xg: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Transform API-Football response to internal fixtures format.

        API-Football v3 response format:
        {
          "response": [
            {
              "fixture": { "id": 123, "date": "2024-01-01" },
              "teams": {
                "home": { "id": 1, "name": "Team A" },
                "away": { "id": 2, "name": "Team B" }
              },
              "goals": { "home": 2, "away": 1 },
              "score": {
                "extratime": { "home": null, "away": null },
                "penalty": { "home": null, "away": null }
              }
            }
          ]
        }

        Args:
            api_response: Raw API-Football response
            team_id: Team ID to extract stats for (determines perspective)
            fetch_xg: If True, fetch xG from statistics endpoint (costs extra API call per fixture)

        Returns:
            List of fixture dictionaries with keys:
                - goals_for: int
                - goals_against: int
                - xg: Optional[float] (may be None if not available)
                - result: str ("W", "D", or "L")
        """
        fixtures = []

        for match in api_response.get("response", []):
            # Determine if team was home or away
            is_home = match["teams"]["home"]["id"] == team_id

            # Extract goals
            goals_home = match["goals"]["home"]
            goals_away = match["goals"]["away"]

            if goals_home is None or goals_away is None:
                # Match not finished yet - skip
                continue

            # Determine result from team's perspective
            if is_home:
                goals_for = goals_home
                goals_against = goals_away
            else:
                goals_for = goals_away
                goals_against = goals_home

            # Determine result
            if goals_for > goals_against:
                result = "W"
            elif goals_for < goals_against:
                result = "L"
            else:
                result = "D"

            # Extract xG if requested
            xg = None
            if fetch_xg:
                fixture_id = match["fixture"]["id"]
                stats = self.fetch_fixture_statistics(fixture_id)
                if stats:
                    xg = self.extract_xg_from_statistics(stats, team_id)
                    if xg:
                        logger.info(f"✅ xG extracted for fixture {fixture_id}: {xg}")

            fixtures.append(
                {
                    "goals_for": goals_for,
                    "goals_against": goals_against,
                    "xg": xg,
                    "result": result,
                    "fixture_id": match["fixture"]["id"],
                }
            )

        return fixtures

    def compute_metrics(self, fixtures: List[Dict[str, Any]]) -> TeamStatistics:
        """
        Calculate team metrics from fixtures with missing data handling.

        Args:
            fixtures: List of fixture dictionaries with keys:
                - goals_for: int
                - goals_against: int
                - xg: Optional[float]
                - result: str ("W", "D", or "L")

        Returns:
            TeamStatistics with calculated metrics
        """
        # Extract xG values (exclude None)
        xg_values = [f["xg"] for f in fixtures if f.get("xg") is not None]

        # Calculate clean sheets
        clean_sheets = sum(1 for f in fixtures if f.get("goals_against") == 0)

        # Generate form string (reversed to show most recent first)
        form_string = "-".join([f["result"] for f in reversed(fixtures)])

        # Handle missing xG data
        if len(xg_values) == 0:
            # ALL matches missing xG - use fallback mode
            return TeamStatistics(
                avg_xg=None,
                clean_sheets=clean_sheets,
                form_string=form_string,
                data_completeness=0.0,
                confidence="low",
                fallback_mode="traditional_form",
            )

        # Calculate metrics with available xG data
        avg_xg = sum(xg_values) / len(xg_values)
        data_completeness = len(xg_values) / len(fixtures)

        # Determine confidence level
        if data_completeness == 1.0:
            confidence = "high"
        elif data_completeness >= 0.5:
            confidence = "medium"
        else:
            confidence = "low"

        return TeamStatistics(
            avg_xg=avg_xg,
            clean_sheets=clean_sheets,
            form_string=form_string,
            data_completeness=data_completeness,
            confidence=confidence,
        )

    def get_cached_stats(self, team_id: int) -> Optional[Dict[str, Any]]:
        """
        Load team stats from local cache if fresh (< 24 hours).

        Cache file naming: cache/team_stats_{team_id}_{YYYY-MM-DD}.json
        Using date in filename naturally expires cache when day changes.

        Args:
            team_id: Team ID to load

        Returns:
            Cached stats dict or None if cache miss/expired
        """
        today = datetime.now().strftime("%Y-%m-%d")
        cache_file = Path(self.cache_dir) / f"team_stats_{team_id}_{today}.json"

        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    stats = json.load(f)
                    logger.info(f"Cache HIT for team {team_id}")
                    return stats
            except (json.JSONDecodeError, IOError) as e:
                # Corrupted cache file - treat as miss
                logger.warning(f"Cache file corrupted for team {team_id}: {e}")
                return None

        logger.info(f"Cache MISS for team {team_id}")
        return None

    def save_to_cache(self, team_id: int, stats: Dict[str, Any]) -> None:
        """
        Save team stats to local cache.

        Creates cache directory if missing.

        Args:
            team_id: Team ID
            stats: Statistics dictionary to cache
        """
        try:
            # Create cache directory if it doesn't exist
            cache_path = Path(self.cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)

            today = datetime.now().strftime("%Y-%m-%d")
            cache_file = cache_path / f"team_stats_{team_id}_{today}.json"

            with open(cache_file, "w") as f:
                json.dump(stats, f, indent=2)

            logger.info(f"Saved cache for team {team_id}")
        except (IOError, OSError) as e:
            logger.error(f"Failed to save cache for team {team_id}: {e}")

    def fetch_from_api(
        self, team_id: int, last: int = 5, next: int = 0
    ) -> Dict[str, Any]:
        """
        Fetch team fixtures from API-Football v3.

        Fetches past and/or upcoming matches for the specified team.

        Args:
            team_id: Team ID to fetch (API-Football team ID)
            last: Number of last (completed) fixtures to fetch (default: 5)
            next: Number of upcoming fixtures to fetch (default: 0)

        Returns:
            API response dictionary with fixtures data

        Raises:
            requests.HTTPError: On HTTP errors (429, 5xx, etc.)
            requests.RequestException: On network/connection errors
        """
        # API-Football v3 endpoint
        url = "https://v3.football.api-sports.io/fixtures"

        # Request headers with API key
        headers = {
            "x-rapidapi-key": config.API_FOOTBALL_KEY,
            "x-rapidapi-host": "v3.football.api-sports.io",
        }

        # Query parameters: last N fixtures and/or next M fixtures for team
        params = {"team": team_id}
        if last > 0:
            params["last"] = last
        if next > 0:
            params["next"] = next

        logger.debug(
            f"Calling API-Football: GET {url}?team={team_id}&last={last}&next={next}"
        )

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()  # Raise HTTPError for bad status codes

            data = response.json()

            # API-Football v3 response format: { "response": [...] }
            if "response" not in data:
                raise ValueError(f"Unexpected API-Football response format: {data}")

            logger.debug(
                f"API-Football returned {len(data.get('response', []))} fixtures"
            )
            return data

        except requests.HTTPError as e:
            # Check for rate limit error (429)
            if e.response.status_code == 429:
                logger.error(f"API-Football rate limit exceeded: {e}")
                raise APIRateLimitError(f"API-Football rate limit (429): {e}") from e
            else:
                logger.error(f"API-Football HTTP error: {e}")
                raise
        except requests.RequestException as e:
            logger.error(f"API-Football request failed: {e}")
            raise

    def fetch_team_stats(self, team_id: int, fetch_xg: bool = True) -> Dict[str, Any]:
        """
        Fetch and compute team statistics with rate limiting and retry logic.

        Implements:
        - 0.5 second delay between requests (RULES.md requirement)
        - Exponential backoff on failures (1s, 2s, 4s)
        - Max 3 retries
        - Automatic metrics computation from API response
        - Optional xG fetching (costs extra API calls)

        Args:
            team_id: Team ID to fetch
            fetch_xg: If True, fetch xG from statistics endpoint (default: True)

        Returns:
            Stats dictionary with computed metrics:
                - avg_xg: Optional[float]
                - clean_sheets: int
                - form_string: str
                - data_completeness: float
                - confidence: str
                - fallback_mode: Optional[str]

        Raises:
            DataAggregationError: After 4 total attempts (max retries exceeded)
            APIRateLimitError: On 429 rate limit errors
        """
        max_retries = 3
        retry_delays = [1, 2, 4]

        logger.info(f"Fetching stats for team {team_id} (fetch_xg={fetch_xg})")
        start_time = time.time()

        for attempt in range(max_retries + 1):
            # Rate limiting: 0.5s delay between requests
            # Sleep on all requests except the very first one
            if self.last_request_time > 0:
                time.sleep(0.5)
                logger.debug(f"Rate limit delay: 0.5s")

            try:
                # Fetch raw API response (last 5 matches)
                api_response = self.fetch_from_api(team_id, last=5, next=0)
                self.last_request_time = time.time()

                # Transform API response to internal format (with optional xG fetching)
                fixtures = self.transform_api_response(
                    api_response, team_id, fetch_xg=fetch_xg
                )

                # Compute metrics
                stats = self.compute_metrics(fixtures)

                # Convert dataclass to dict for caching
                result = {
                    "avg_xg": stats.avg_xg,
                    "clean_sheets": stats.clean_sheets,
                    "form_string": stats.form_string,
                    "data_completeness": stats.data_completeness,
                    "confidence": stats.confidence,
                    "fallback_mode": stats.fallback_mode,
                    "has_real_data": True,  # Data fetched from API-Football
                }

                elapsed = time.time() - start_time
                logger.info(
                    f"API call SUCCESS for team {team_id} (attempt {attempt + 1}, elapsed {elapsed:.2f}s, {len(fixtures)} fixtures)"
                )
                return result

            except Exception as e:
                error_msg = str(e)
                elapsed = time.time() - start_time

                # Check for rate limit error
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    logger.warning(
                        f"Rate limit hit for team {team_id} (attempt {attempt + 1})"
                    )
                    if attempt == max_retries:
                        raise APIRateLimitError(
                            f"Rate limit exceeded for team {team_id}"
                        )

                # On last attempt, raise final exception
                if attempt == max_retries:
                    logger.error(
                        f"API call FAILED for team {team_id} after {attempt + 1} attempts (elapsed {elapsed:.2f}s): {error_msg}"
                    )
                    raise DataAggregationError(team_id, "Max retries exceeded") from e

                # Exponential backoff
                delay = retry_delays[attempt]
                logger.warning(
                    f"API call failed (attempt {attempt + 1}), retrying in {delay}s: {error_msg}"
                )
                time.sleep(delay)

        # Should never reach here, but satisfy type checker
        raise DataAggregationError(team_id, "Max retries exceeded")

    def fetch_team_fixtures(
        self, team_id: int, last: int = 5, next: int = 5
    ) -> Dict[str, Any]:
        """
        Fetch both past and upcoming fixtures for a team.

        NOTE: API-Football does not support using 'last' and 'next' parameters
        together, so this method makes TWO separate API calls.

        Args:
            team_id: API-Football team ID
            last: Number of completed fixtures to fetch
            next: Number of upcoming fixtures to fetch

        Returns:
            Dictionary with:
                - past_fixtures: List of completed match dicts
                - upcoming_fixtures: List of upcoming match dicts
                - total_count: Total number of fixtures returned

        Raises:
            DataAggregationError: After max retries exceeded
            APIRateLimitError: On 429 rate limit errors
        """
        logger.info(f"Fetching fixtures for team {team_id} (last={last}, next={next})")
        start_time = time.time()

        past_fixtures = []
        upcoming_fixtures = []

        # Fetch past fixtures (if requested)
        if last > 0:
            past_fixtures = self._fetch_fixtures_by_type(
                team_id, last=last, fetch_type="past"
            )

        # Fetch upcoming fixtures (if requested)
        if next > 0:
            upcoming_fixtures = self._fetch_fixtures_by_type(
                team_id, next=next, fetch_type="upcoming"
            )

        result = {
            "past_fixtures": past_fixtures,
            "upcoming_fixtures": upcoming_fixtures,
            "total_count": len(past_fixtures) + len(upcoming_fixtures),
        }

        elapsed = time.time() - start_time
        logger.info(
            f"Fixtures fetch SUCCESS for team {team_id} "
            f"(elapsed {elapsed:.2f}s, {len(past_fixtures)} past, {len(upcoming_fixtures)} upcoming)"
        )
        return result

    def _fetch_fixtures_by_type(
        self, team_id: int, last: int = 0, next: int = 0, fetch_type: str = "past"
    ) -> List[Dict[str, Any]]:
        """
        Internal method to fetch either past or upcoming fixtures.

        Args:
            team_id: API-Football team ID
            last: Number of completed fixtures (use for past)
            next: Number of upcoming fixtures (use for upcoming)
            fetch_type: "past" or "upcoming" (for logging)

        Returns:
            List of fixture dictionaries

        Raises:
            DataAggregationError: After max retries exceeded
            APIRateLimitError: On 429 rate limit errors
        """
        max_retries = 3
        retry_delays = [1, 2, 4]

        for attempt in range(max_retries + 1):
            # Rate limiting: 0.5s delay between requests
            if self.last_request_time > 0:
                time.sleep(0.5)
                logger.debug(f"Rate limit delay: 0.5s")

            try:
                # Fetch raw API response
                api_response = self.fetch_from_api(team_id, last=last, next=next)
                self.last_request_time = time.time()

                # Parse fixtures
                fixtures = []
                for match in api_response.get("response", []):
                    fixture_data = {
                        "fixture_id": match["fixture"]["id"],
                        "date": match["fixture"]["date"],
                        "venue": match["fixture"]["venue"]["name"],
                        "status": match["fixture"]["status"]["short"],
                        "league": match["league"]["name"],
                        "home_team": {
                            "id": match["teams"]["home"]["id"],
                            "name": match["teams"]["home"]["name"],
                        },
                        "away_team": {
                            "id": match["teams"]["away"]["id"],
                            "name": match["teams"]["away"]["name"],
                        },
                    }

                    # Add goals if match is finished
                    if match["goals"]["home"] is not None:
                        fixture_data["goals"] = {
                            "home": match["goals"]["home"],
                            "away": match["goals"]["away"],
                        }

                    fixtures.append(fixture_data)

                logger.debug(
                    f"Fetched {len(fixtures)} {fetch_type} fixtures for team {team_id}"
                )
                return fixtures

            except Exception as e:
                error_msg = str(e)

                # Check for rate limit error
                if "429" in error_msg or "rate limit" in error_msg.lower():
                    logger.warning(
                        f"Rate limit hit for team {team_id} (attempt {attempt + 1})"
                    )
                    if attempt == max_retries:
                        raise APIRateLimitError(
                            f"Rate limit exceeded for team {team_id}"
                        )

                # On last attempt, raise final exception
                if attempt == max_retries:
                    logger.error(
                        f"{fetch_type.capitalize()} fixtures fetch FAILED for team {team_id} "
                        f"after {attempt + 1} attempts: {error_msg}"
                    )
                    raise DataAggregationError(team_id, "Max retries exceeded") from e

                # Exponential backoff
                delay = retry_delays[attempt]
                logger.warning(
                    f"Fixtures fetch failed (attempt {attempt + 1}), retrying in {delay}s: {error_msg}"
                )
                time.sleep(delay)

        # Should never reach here, but satisfy type checker
        raise DataAggregationError(team_id, "Max retries exceeded")

    def fetch_match_prediction(self, fixture_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch API-Football's prediction for a specific fixture.

        Args:
            fixture_id: API-Football fixture ID

        Returns:
            Dict with prediction data including:
            - predictions.winner (home/away/draw with probabilities)
            - predictions.goals (over/under percentages)
            - comparison (form, attack, defense, poisson)
            - teams (head-to-head data)

            Returns None if no prediction available or error occurs.
        """
        cache_key = f"prediction_{fixture_id}"

        # Check cache first
        cached = self.get_cached_stats(cache_key)
        if cached:
            logger.info(f"✅ Cache HIT for prediction {fixture_id}")
            return cached

        # Rate limiting
        self._enforce_rate_limit()

        # API call
        url = "https://v3.football.api-sports.io/predictions"
        headers = {"x-apisports-key": config.API_FOOTBALL_KEY}
        params = {"fixture": fixture_id}

        try:
            logger.info(f"🌐 Fetching prediction for fixture {fixture_id}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data.get("response"):
                logger.warning(f"No prediction available for fixture {fixture_id}")
                return None

            prediction_data = data["response"][0]

            # Cache the result
            self.save_cached_stats(cache_key, prediction_data)

            logger.info(f"✅ Prediction fetched for fixture {fixture_id}")
            return prediction_data

        except Exception as e:
            logger.error(f"Failed to fetch prediction for fixture {fixture_id}: {e}")
            return None

    def fetch_fixture_statistics(self, fixture_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch detailed match statistics including xG.

        Args:
            fixture_id: API-Football fixture ID

        Returns:
            Dict with statistics for both teams including:
            - Expected Goals (xG)
            - Shots on target
            - Possession
            - Passes
            - Tackles

            Returns None if no statistics available.
        """
        cache_key = f"stats_{fixture_id}"

        # Check cache first
        cached = self.get_cached_stats(cache_key)
        if cached:
            logger.info(f"✅ Cache HIT for statistics {fixture_id}")
            return cached

        # Rate limiting
        self._enforce_rate_limit()

        # API call
        url = "https://v3.football.api-sports.io/fixtures/statistics"
        headers = {"x-apisports-key": config.API_FOOTBALL_KEY}
        params = {"fixture": fixture_id}

        try:
            logger.info(f"🌐 Fetching statistics for fixture {fixture_id}...")
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if not data.get("response"):
                logger.warning(f"No statistics available for fixture {fixture_id}")
                return None

            stats_data = data["response"]

            # Cache the result
            self.save_cached_stats(cache_key, stats_data)

            logger.info(f"✅ Statistics fetched for fixture {fixture_id}")
            return stats_data

        except Exception as e:
            logger.error(f"Failed to fetch statistics for fixture {fixture_id}: {e}")
            return None

    def extract_xg_from_statistics(
        self, statistics: List[Dict[str, Any]], team_id: int
    ) -> Optional[float]:
        """
        Extract xG (expected goals) for a specific team from match statistics.

        Args:
            statistics: Statistics response from API-Football
            team_id: API-Football team ID to extract xG for

        Returns:
            xG value as float, or None if not available
        """
        try:
            # Find team's statistics
            team_stats = next(
                (s for s in statistics if s["team"]["id"] == team_id), None
            )

            if not team_stats:
                return None

            # Find expected goals statistic
            stats_list = team_stats.get("statistics", [])
            xg_stat = next(
                (s for s in stats_list if s["type"] == "expected_goals"), None
            )

            if xg_stat and xg_stat.get("value"):
                return float(xg_stat["value"])

            return None

        except (KeyError, ValueError, TypeError) as e:
            logger.warning(f"Failed to extract xG: {e}")
            return None

    def _enforce_rate_limit(self):
        """Enforce 0.5 second delay between API requests."""
        elapsed = time.time() - self.last_request_time
        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)
        self.last_request_time = time.time()
