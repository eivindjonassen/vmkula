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
