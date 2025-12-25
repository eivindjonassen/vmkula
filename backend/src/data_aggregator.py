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

    def fetch_from_api(self, team_id: int) -> Dict[str, Any]:
        """
        Raw API call to API-Football (mockable for testing).

        This method is designed to be mocked in tests.
        Real implementation would call API-Football endpoints.

        Args:
            team_id: Team ID to fetch

        Returns:
            API response dictionary

        Raises:
            Exception: On API errors (429, 5xx, etc.)
        """
        # This is a placeholder for the actual API call
        # In production, this would use requests.get() with proper headers
        raise NotImplementedError(
            "API-Football integration not yet implemented - use mocks for testing"
        )

    def fetch_team_stats(self, team_id: int) -> Dict[str, Any]:
        """
        Fetch team stats with rate limiting and retry logic.

        Implements:
        - 0.5 second delay between requests (RULES.md requirement)
        - Exponential backoff on failures (1s, 2s, 4s)
        - Max 3 retries

        Args:
            team_id: Team ID to fetch

        Returns:
            Stats dictionary from API

        Raises:
            DataAggregationError: After 4 total attempts (max retries exceeded)
            APIRateLimitError: On 429 rate limit errors
        """
        max_retries = 3
        retry_delays = [1, 2, 4]

        logger.info(f"Fetching stats for team {team_id}")
        start_time = time.time()

        for attempt in range(max_retries + 1):
            # Rate limiting: 0.5s delay between requests
            # Sleep on all requests except the very first one
            if self.last_request_time > 0:
                time.sleep(0.5)
                logger.debug(f"Rate limit delay: 0.5s")

            try:
                result = self.fetch_from_api(team_id)
                self.last_request_time = time.time()
                elapsed = time.time() - start_time
                logger.info(
                    f"API call SUCCESS for team {team_id} (attempt {attempt + 1}, elapsed {elapsed:.2f}s)"
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
