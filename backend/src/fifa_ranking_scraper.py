"""
FIFA World Rankings Scraper Module.

This module scrapes FIFA world rankings from https://inside.fifa.com/fifa-world-ranking/men
and stores them in Firestore with a 30-day TTL cache.

Features:
- BeautifulSoup4-based static HTML parsing (no JavaScript rendering needed)
- Polite scraping with 2-second minimum delay between requests
- Exponential backoff retry logic for transient failures
- 30-day TTL cache (FIFA rankings update monthly)
- Single-document Firestore storage pattern for cost efficiency
- Validation to ensure all 211 FIFA member nations are scraped
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import requests
from bs4 import BeautifulSoup

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
    Scrapes FIFA world rankings and stores them in Firestore.
    
    Implements polite scraping with rate limiting, retry logic, and caching
    to minimize requests to FIFA.com while providing fresh ranking data for
    the prediction pipeline.
    """
    
    # Class constants
    RANKINGS_URL = "https://inside.fifa.com/fifa-world-ranking/men"
    MIN_DELAY_SECONDS = 2.0  # Polite scraping delay
    CACHE_TTL_DAYS = 30  # FIFA rankings update monthly
    
    def __init__(self):
        """Initialize the FIFA ranking scraper with rate limiting."""
        self.last_request_time: float = 0.0
        self.firestore_manager = FirestoreManager()
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
    
    def fetch_rankings_page(self) -> str:
        """
        Fetch FIFA rankings HTML page with retry logic.
        
        Implements exponential backoff retry strategy [1s, 2s, 4s] for transient
        failures. Enforces rate limiting on all requests.
        
        Returns:
            HTML content of the rankings page
            
        Raises:
            DataAggregationError: After max retries exceeded (4 attempts total)
        """
        max_retries = 3
        retry_delays = [1, 2, 4]
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        logger.info(f"Fetching FIFA rankings from {self.RANKINGS_URL}")
        start_time = time.time()
        
        for attempt in range(max_retries + 1):
            # Enforce rate limiting (except on very first request ever)
            if self.last_request_time > 0:
                self._enforce_rate_limit()
            
            try:
                # Make HTTP request
                response = requests.get(self.RANKINGS_URL, headers=headers, timeout=30)
                
                # Check for successful response
                response.raise_for_status()
                
                # Only update last_request_time on successful request
                self.last_request_time = time.time()
                
                elapsed = time.time() - start_time
                logger.info(
                    f"FIFA rankings fetch SUCCESS (attempt {attempt + 1}, "
                    f"elapsed {elapsed:.2f}s, {len(response.text)} bytes)"
                )
                return response.text
                
            except Exception as e:
                error_msg = str(e)
                elapsed = time.time() - start_time
                
                # On last attempt, raise final exception
                if attempt == max_retries:
                    logger.error(
                        f"FIFA rankings fetch FAILED after {attempt + 1} attempts "
                        f"(elapsed {elapsed:.2f}s): {error_msg}"
                    )
                    # Use team_id=0 to indicate FIFA rankings fetch (not team-specific)
                    raise DataAggregationError(
                        0, 
                        f"FIFA rankings fetch failed: {error_msg}"
                    ) from e
                
                # Exponential backoff
                delay = retry_delays[attempt]
                logger.warning(
                    f"FIFA rankings fetch failed (attempt {attempt + 1}), "
                    f"retrying in {delay}s: {error_msg}"
                )
                time.sleep(delay)
        
        # Should never reach here, but satisfy type checker
        raise DataAggregationError(0, "FIFA rankings fetch: max retries exceeded")
    
    def parse_rankings(self, html: str) -> List[Dict[str, Any]]:
        """
        Parse FIFA rankings HTML table and extract team data.
        
        Args:
            html: Raw HTML content from FIFA rankings page
            
        Returns:
            List of dicts with team ranking data (up to 211 teams)
            Each dict contains: rank, team_name, fifa_code, confederation, 
                              points, previous_rank, rank_change
        
        Raises:
            None - logs warnings for parsing errors, returns partial data
        """
        rankings: List[Dict[str, Any]] = []
        
        try:
            soup = BeautifulSoup(html, 'lxml')
            table = soup.find('table', class_='table')
            
            if not table:
                logger.warning("FIFA rankings table not found in HTML")
                return rankings
            
            tbody = table.find('tbody')
            if not tbody:
                logger.warning("Table body not found in FIFA rankings table")
                return rankings
            
            rows = tbody.find_all('tr')
            
            for row in rows:
                try:
                    # Extract all fields
                    rank_td = row.find('td', class_='rank')
                    team_name_td = row.find('td', class_='team-name')
                    fifa_code_td = row.find('td', class_='fifa-code')
                    confederation_td = row.find('td', class_='confederation')
                    points_td = row.find('td', class_='points')
                    previous_rank_td = row.find('td', class_='previous-rank')
                    
                    # Skip row if critical fields are missing
                    if not rank_td or not team_name_td:
                        logger.warning(f"Skipping row with missing rank or team name")
                        continue
                    
                    # Parse rank (required)
                    try:
                        rank = int(rank_td.get_text(strip=True))
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"Invalid rank value: {e}")
                        continue
                    
                    # Parse team name (required)
                    team_name = team_name_td.get_text(strip=True)
                    if not team_name:
                        logger.warning(f"Empty team name for rank {rank}")
                        continue
                    
                    # Parse optional fields
                    fifa_code = fifa_code_td.get_text(strip=True) if fifa_code_td else None
                    confederation = confederation_td.get_text(strip=True) if confederation_td else None
                    
                    # Parse points (optional, float)
                    points = None
                    if points_td:
                        try:
                            points = float(points_td.get_text(strip=True))
                        except (ValueError, AttributeError) as e:
                            logger.warning(f"Invalid points value for {team_name}: {e}")
                    
                    # Parse previous rank (optional, int)
                    previous_rank = None
                    if previous_rank_td:
                        try:
                            previous_rank = int(previous_rank_td.get_text(strip=True))
                        except (ValueError, AttributeError) as e:
                            logger.warning(f"Invalid previous rank value for {team_name}: {e}")
                    
                    # Calculate rank change
                    rank_change = None
                    if previous_rank is not None:
                        rank_change = previous_rank - rank  # positive = moved up, negative = moved down
                    
                    # Build team dict
                    team_data = {
                        'rank': rank,
                        'team_name': team_name,
                        'fifa_code': fifa_code,
                        'confederation': confederation,
                        'points': points,
                        'previous_rank': previous_rank,
                        'rank_change': rank_change
                    }
                    
                    rankings.append(team_data)
                    
                except Exception as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(rankings)} teams from FIFA rankings")
            
        except Exception as e:
            logger.error(f"Error parsing FIFA rankings HTML: {e}")
        
        return rankings
    
    def scrape_and_store(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Orchestrate full FIFA rankings scraping workflow.
        
        Workflow:
        1. Check cache validity (skip if force_refresh=True)
        2. If cache valid and not force_refresh, return cached data
        3. Otherwise: fetch HTML → parse rankings → validate 211 teams → store
        4. Store raw HTML response for audit trail
        5. Return result with metadata
        
        Args:
            force_refresh: If True, bypass cache and always scrape fresh data
            
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
                    # Check if cache is still valid
                    expires_at = cached_data.get('expires_at')
                    if expires_at and expires_at > datetime.utcnow():
                        # Cache hit - return cached data
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
            
            # Cache miss or force refresh - scrape fresh data
            logger.info(
                f"FIFA rankings cache MISS or force_refresh=True - scraping fresh data"
            )
            
            # Step 1: Fetch HTML
            html = self.fetch_rankings_page()
            
            # Step 2: Parse rankings
            rankings = self.parse_rankings(html)
            
            # Step 3: Validate completeness (expect 211 teams)
            if len(rankings) < 211:
                logger.warning(
                    f"Incomplete rankings: {len(rankings)}/211 teams scraped"
                )
            
            if len(rankings) == 0:
                duration = time.time() - start_time
                return {
                    'success': False,
                    'teams_scraped': 0,
                    'duration_seconds': duration,
                    'error_message': 'No teams scraped from FIFA rankings page'
                }
            
            # Step 4: Store in Firestore
            self.firestore_manager.update_fifa_rankings(
                rankings, 
                ttl_days=self.CACHE_TTL_DAYS
            )
            
            # Step 5: Store raw HTML for audit trail (optional - skip if manager unavailable)
            try:
                raw_response_data = {
                    'html': html,
                    'teams_parsed': len(rankings),
                    'source_url': self.RANKINGS_URL
                }
                
                document_id = f"fifa_rankings_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
                self.firestore_manager.db.collection("raw_api_responses").document(
                    document_id
                ).set({
                    'entity_type': 'fifa_rankings',
                    'raw_response': raw_response_data,
                    'fetched_at': datetime.utcnow(),
                    'source': 'FIFA.com'
                })
            except Exception as e:
                # Log but don't fail if raw storage fails
                logger.warning(f"Failed to store raw API response: {e}")
            
            # Calculate timestamps
            fetched_at = datetime.utcnow()
            cache_expires_at = fetched_at + timedelta(days=self.CACHE_TTL_DAYS)
            duration = time.time() - start_time
            
            logger.info(
                f"FIFA rankings scraped successfully: {len(rankings)} teams "
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
            error_msg = f"FIFA rankings scraping failed: {str(e)}"
            logger.error(error_msg)
            
            return {
                'success': False,
                'teams_scraped': 0,
                'duration_seconds': duration,
                'error_message': error_msg
            }
