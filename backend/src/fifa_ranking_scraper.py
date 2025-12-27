"""
FIFA World Rankings Scraper Module.

This module fetches FIFA world rankings from the FIFA API and stores them
in Firestore with a 30-day TTL cache.

Features:
- Direct FIFA API access (more reliable than HTML scraping)
- Two-step fetch: page metadata for dateId, then API for rankings
- Polite scraping with 2-second minimum delay between requests
- Exponential backoff retry logic for transient failures
- 30-day TTL cache (FIFA rankings update monthly)
- Single-document Firestore storage pattern for cost efficiency
- Validation to ensure all 211 FIFA member nations are fetched
"""

import logging
import re
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import requests

from src.exceptions import DataAggregationError
from src.firestore_manager import FirestoreManager

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class FIFARankingScraper:
    """
    Fetches FIFA world rankings via API and stores them in Firestore.
    
    Implements polite scraping with rate limiting, retry logic, and caching
    to minimize requests to FIFA.com while providing fresh ranking data for
    the prediction pipeline.
    """
    
    # Class constants
    RANKINGS_PAGE_URL = "https://inside.fifa.com/fifa-world-ranking/men"
    RANKINGS_API_URL = "https://inside.fifa.com/api/ranking-overview"
    MIN_DELAY_SECONDS = 2.0  # Polite scraping delay
    CACHE_TTL_DAYS = 30  # FIFA rankings update monthly
    
    def __init__(self):
        """Initialize the FIFA ranking scraper with rate limiting."""
        self.last_request_time: float = 0.0
        self.firestore_manager = FirestoreManager()
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Referer': self.RANKINGS_PAGE_URL
        }
        logger.info("FIFARankingScraper initialized")
    
    def _enforce_rate_limit(self) -> None:
        """
        Enforce minimum delay between requests (polite scraping).
        
        Sleeps if insufficient time has elapsed since last request to ensure
        MIN_DELAY_SECONDS (2.0s) between requests to FIFA.com.
        """
        elapsed = time.time() - self.last_request_time
        if elapsed < self.MIN_DELAY_SECONDS:
            sleep_time = self.MIN_DELAY_SECONDS - elapsed
            logger.debug(f"Rate limit: sleeping {sleep_time:.2f}s")
            time.sleep(sleep_time)
    
    def _make_request(self, url: str, accept_html: bool = False) -> requests.Response:
        """
        Make an HTTP request with rate limiting and retry logic.
        
        Args:
            url: URL to fetch
            accept_html: If True, accept HTML response; otherwise JSON
            
        Returns:
            Response object
            
        Raises:
            DataAggregationError: After max retries exceeded
        """
        max_retries = 3
        retry_delays = [1, 2, 4]
        
        headers = self._headers.copy()
        if accept_html:
            headers['Accept'] = 'text/html,application/xhtml+xml'
        
        start_time = time.time()
        
        for attempt in range(max_retries + 1):
            # Enforce rate limiting (except on very first request ever)
            if self.last_request_time > 0:
                self._enforce_rate_limit()
            
            try:
                response = requests.get(url, headers=headers, timeout=30)
                response.raise_for_status()
                
                self.last_request_time = time.time()
                elapsed = time.time() - start_time
                
                logger.info(
                    f"Request SUCCESS: {url[:60]}... (attempt {attempt + 1}, "
                    f"elapsed {elapsed:.2f}s)"
                )
                return response
                
            except Exception as e:
                error_msg = str(e)
                elapsed = time.time() - start_time
                
                if attempt == max_retries:
                    logger.error(
                        f"Request FAILED after {attempt + 1} attempts "
                        f"(elapsed {elapsed:.2f}s): {error_msg}"
                    )
                    raise DataAggregationError(
                        0, 
                        f"FIFA request failed: {error_msg}"
                    ) from e
                
                delay = retry_delays[attempt]
                logger.warning(
                    f"Request failed (attempt {attempt + 1}), "
                    f"retrying in {delay}s: {error_msg}"
                )
                time.sleep(delay)
        
        raise DataAggregationError(0, "FIFA request: max retries exceeded")
    
    def _get_latest_date_id(self) -> str:
        """
        Fetch the latest ranking dateId from the FIFA page metadata.
        
        The FIFA rankings page embeds __NEXT_DATA__ JSON with available
        ranking dates. We extract the latest dateId to use in API calls.
        
        Returns:
            Latest dateId string (e.g., "id14962")
            
        Raises:
            DataAggregationError: If dateId cannot be extracted
        """
        logger.info("Fetching latest FIFA ranking dateId...")
        
        response = self._make_request(self.RANKINGS_PAGE_URL, accept_html=True)
        html = response.text
        
        # Extract __NEXT_DATA__ JSON from page
        next_data_match = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', 
            html, 
            re.DOTALL
        )
        
        if not next_data_match:
            raise DataAggregationError(0, "Could not find __NEXT_DATA__ in FIFA page")
        
        try:
            next_data = json.loads(next_data_match.group(1))
            page_data = next_data['props']['pageProps']['pageData']
            ranking = page_data['ranking']
            dates = ranking.get('dates', [])
            
            if not dates:
                raise DataAggregationError(0, "No ranking dates found in FIFA page data")
            
            # Get the latest date (first year, first date)
            latest_year = dates[0]
            latest_dates = latest_year.get('dates', [])
            
            if not latest_dates:
                raise DataAggregationError(0, "No dates in latest year")
            
            date_id = latest_dates[0].get('id')
            date_text = latest_dates[0].get('dateText', 'unknown')
            
            logger.info(f"Found latest dateId: {date_id} ({date_text})")
            return date_id
            
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            raise DataAggregationError(
                0, 
                f"Failed to parse FIFA page data for dateId: {e}"
            ) from e
    
    def fetch_rankings_from_api(self, date_id: str) -> List[Dict[str, Any]]:
        """
        Fetch rankings from FIFA API for a specific date.
        
        Args:
            date_id: FIFA ranking date identifier (e.g., "id14962")
            
        Returns:
            List of team ranking dicts with normalized structure
        """
        api_url = f"{self.RANKINGS_API_URL}?locale=en&dateId={date_id}"
        
        logger.info(f"Fetching rankings from FIFA API with dateId={date_id}")
        
        response = self._make_request(api_url)
        data = response.json()
        
        raw_rankings = data.get('rankings', [])
        logger.info(f"API returned {len(raw_rankings)} teams")
        
        # Normalize the API response to our standard format
        rankings = []
        for item in raw_rankings:
            try:
                ranking_item = item.get('rankingItem', {})
                tag = item.get('tag', {})
                
                rank = ranking_item.get('rank')
                team_name = ranking_item.get('name')
                
                if rank is None or not team_name:
                    logger.warning(f"Skipping item with missing rank or name: {item}")
                    continue
                
                previous_rank = ranking_item.get('previousRank')
                rank_change = None
                if previous_rank is not None:
                    rank_change = previous_rank - rank
                
                team_data = {
                    'rank': rank,
                    'team_name': team_name,
                    'fifa_code': ranking_item.get('countryCode'),
                    'confederation': tag.get('id'),
                    'points': ranking_item.get('totalPoints'),
                    'previous_rank': previous_rank,
                    'previous_points': item.get('previousPoints'),
                    'rank_change': rank_change,
                    'fifa_team_id': ranking_item.get('idTeam'),
                    'flag_url': ranking_item.get('flag', {}).get('src'),
                }
                
                rankings.append(team_data)
                
            except Exception as e:
                logger.warning(f"Error parsing ranking item: {e}")
                continue
        
        return rankings
    
    # Keep legacy method for backward compatibility
    def fetch_rankings_page(self) -> str:
        """
        Fetch FIFA rankings HTML page (legacy method).
        
        Note: This method is kept for backward compatibility but the API
        approach (fetch_rankings_from_api) is now preferred.
        """
        response = self._make_request(self.RANKINGS_PAGE_URL, accept_html=True)
        return response.text
    
    def parse_rankings(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse FIFA rankings from HTML (legacy method).
        
        Note: This method is kept for backward compatibility but returns
        empty list since FIFA now uses a JavaScript SPA. Use the API approach.
        """
        logger.warning(
            "parse_rankings() is deprecated - FIFA uses JavaScript SPA. "
            "Use fetch_rankings_from_api() instead."
        )
        return []
    
    def scrape_and_store(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Orchestrate full FIFA rankings fetch workflow.
        
        Workflow:
        1. Check cache validity (skip if force_refresh=True)
        2. If cache valid and not force_refresh, return cached data
        3. Otherwise: fetch dateId → call API → validate 211 teams → store
        4. Store raw API response for audit trail
        5. Return result with metadata
        
        Args:
            force_refresh: If True, bypass cache and always fetch fresh data
            
        Returns:
            Result dict with:
                - success: bool
                - teams_scraped: int
                - duration_seconds: float
                - fetched_at: datetime
                - cache_expires_at: datetime
                - cache_hit: bool (only if cache used)
                - error_message: str (only if failure)
        """
        start_time = time.time()
        
        try:
            # Check cache validity (unless force refresh)
            if not force_refresh and self.firestore_manager:
                cached_data = self.firestore_manager.get_fifa_rankings()
                
                if cached_data:
                    expires_at = cached_data.get('expires_at')
                    if expires_at and expires_at > datetime.utcnow():
                        duration = time.time() - start_time
                        logger.info(
                            f"FIFA rankings cache HIT (expires: {expires_at.strftime('%Y-%m-%d')})"
                        )
                        return {
                            'success': True,
                            'teams_scraped': cached_data.get('total_teams', 0),
                            'duration_seconds': duration,
                            'fetched_at': cached_data.get('fetched_at'),
                            'cache_expires_at': expires_at,
                            'cache_hit': True
                        }
            
            # Cache miss or force refresh - fetch fresh data
            logger.info(
                "FIFA rankings cache MISS or force_refresh=True - fetching fresh data"
            )
            
            # Step 1: Get latest dateId from page metadata
            date_id = self._get_latest_date_id()
            
            # Step 2: Fetch rankings from API
            rankings = self.fetch_rankings_from_api(date_id)
            
            # Step 3: Validate completeness (expect 211 teams)
            if len(rankings) < 211:
                logger.warning(
                    f"Incomplete rankings: {len(rankings)}/211 teams fetched"
                )
            
            if len(rankings) == 0:
                duration = time.time() - start_time
                return {
                    'success': False,
                    'teams_scraped': 0,
                    'duration_seconds': duration,
                    'error_message': 'No teams fetched from FIFA API'
                }
            
            # Step 4: Store in Firestore
            self.firestore_manager.update_fifa_rankings(
                rankings, 
                ttl_days=self.CACHE_TTL_DAYS
            )
            
            # Step 5: Store raw API response for audit trail
            try:
                document_id = f"fifa_rankings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                self.firestore_manager.db.collection("raw_api_responses").document(
                    document_id
                ).set({
                    'entity_type': 'fifa_rankings',
                    'raw_response': {
                        'date_id': date_id,
                        'teams_count': len(rankings),
                        'source_url': f"{self.RANKINGS_API_URL}?dateId={date_id}"
                    },
                    'fetched_at': datetime.utcnow(),
                    'source': 'FIFA API'
                })
            except Exception as e:
                logger.warning(f"Failed to store raw API response: {e}")
            
            # Calculate timestamps
            fetched_at = datetime.utcnow()
            cache_expires_at = fetched_at + timedelta(days=self.CACHE_TTL_DAYS)
            duration = time.time() - start_time
            
            logger.info(
                f"FIFA rankings fetched successfully: {len(rankings)} teams "
                f"in {duration:.2f}s"
            )
            
            return {
                'success': True,
                'teams_scraped': len(rankings),
                'duration_seconds': duration,
                'fetched_at': fetched_at,
                'cache_expires_at': cache_expires_at,
                'cache_hit': False
            }
            
        except Exception as e:
            duration = time.time() - start_time
            error_msg = f"FIFA rankings fetch failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'teams_scraped': 0,
                'duration_seconds': duration,
                'error_message': error_msg
            }
    
    def validate_completeness(self, rankings: List[Dict[str, Any]]) -> bool:
        """
        Validate that all 211 FIFA member nations are present in rankings.
        
        Args:
            rankings: List of team ranking dicts
            
        Returns:
            True if 211 teams present, False otherwise
        """
        is_complete = len(rankings) == 211
        
        if not is_complete:
            logger.warning(
                f"Rankings incomplete: {len(rankings)}/211 teams "
                f"({'missing' if len(rankings) < 211 else 'extra'} teams)"
            )
        else:
            logger.info("Rankings validation passed: 211/211 teams present")
        
        return is_complete
    
    def get_ranking_for_team(self, fifa_code: str) -> Optional[Dict[str, Any]]:
        """
        Get ranking data for a specific team by FIFA code.
        
        Args:
            fifa_code: FIFA country code (e.g., 'ARG', 'FRA', 'BRA')
            
        Returns:
            Team ranking dict or None if not found
            Format: {rank, team_name, fifa_code, confederation, points, previous_rank, rank_change}
        """
        try:
            rankings_data = self.firestore_manager.get_fifa_rankings()
            
            if not rankings_data:
                logger.warning(f"No FIFA rankings data available for lookup: {fifa_code}")
                return None
            
            rankings = rankings_data.get('rankings', [])
            
            for team in rankings:
                if team.get('fifa_code') == fifa_code:
                    logger.info(f"Found ranking for {fifa_code}: rank #{team.get('rank')}")
                    return team
            
            logger.warning(f"Team not found in FIFA rankings: {fifa_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error looking up ranking for {fifa_code}: {e}")
            return None
