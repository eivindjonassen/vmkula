"""
Tests for FIFA World Rankings Scraper.

This module tests the FIFARankingScraper class which fetches FIFA world rankings
from the FIFA API and stores them in Firestore.

Test coverage includes:
- Scraper initialization and configuration
- API fetching with retry logic and rate limiting
- Rankings data validation (211 teams expected)
- Firestore storage integration with TTL cache
- Team ranking lookup methods
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import time


# Fixture to mock FirestoreManager before importing FIFARankingScraper
@pytest.fixture
def mock_firestore_manager():
    """Mock FirestoreManager to avoid Google Cloud credential requirements."""
    with patch('src.fifa_ranking_scraper.FirestoreManager') as mock_fm:
        mock_manager = MagicMock()
        mock_fm.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def scraper(mock_firestore_manager):
    """Create a FIFARankingScraper instance with mocked FirestoreManager."""
    from src.fifa_ranking_scraper import FIFARankingScraper
    return FIFARankingScraper()


class TestFIFARankingScraper:
    """Test suite for FIFARankingScraper class."""

    def test_scraper_initialization(self, scraper):
        """
        Test scraper initialization and configuration constants.
        
        Verifies that FIFARankingScraper is initialized with correct:
        - FIFA rankings API URL
        - Minimum delay between requests (polite scraping)
        - Cache TTL (30 days for monthly updates)
        """
        # Verify scraper constants (updated to match actual implementation)
        assert scraper.RANKINGS_PAGE_URL == "https://inside.fifa.com/fifa-world-ranking/men"
        assert scraper.RANKINGS_API_URL == "https://inside.fifa.com/api/ranking-overview"
        assert scraper.MIN_DELAY_SECONDS == 2.0
        assert scraper.CACHE_TTL_DAYS == 30

    def test_fetch_rankings_page_success(self, scraper):
        """
        Test successful HTTP 200 response from FIFA rankings page.
        
        Verifies that fetch_rankings_page():
        - Makes HTTP GET request to FIFA rankings URL
        - Returns HTML content on success
        """
        # Mock successful HTTP response
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html><body>FIFA Rankings</body></html>"
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Execute fetch
            html = scraper.fetch_rankings_page()
            
            # Verify request made
            mock_get.assert_called_once()
            
            # Verify HTML returned
            assert html == "<html><body>FIFA Rankings</body></html>"
    
    def test_fetch_rankings_page_retry_on_failure(self, scraper):
        """
        Test retry logic with exponential backoff on transient failures.
        
        Simulates 503 errors on first 2 attempts, then succeeds on 3rd attempt.
        """
        from src.exceptions import DataAggregationError
        
        # Mock responses: fail twice, then succeed
        with patch('requests.get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # First two calls raise errors
            error_response_1 = Mock()
            error_response_1.raise_for_status.side_effect = Exception("503 Service Unavailable")
            
            error_response_2 = Mock()
            error_response_2.raise_for_status.side_effect = Exception("503 Service Unavailable")
            
            # Third call succeeds
            success_response = Mock()
            success_response.status_code = 200
            success_response.text = "<html>Rankings</html>"
            success_response.raise_for_status = Mock()
            
            mock_get.side_effect = [error_response_1, error_response_2, success_response]
            
            # Execute fetch
            html = scraper.fetch_rankings_page()
            
            # Verify 3 attempts made
            assert mock_get.call_count == 3
            
            # Verify exponential backoff: [1s, 2s]
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(2)
            
            # Verify success on 3rd attempt
            assert html == "<html>Rankings</html>"
    
    def test_fetch_rankings_page_max_retries_exceeded(self, scraper):
        """
        Test that DataAggregationError raised after max retries exceeded.
        """
        from src.exceptions import DataAggregationError
        
        # Mock persistent failures
        with patch('requests.get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # All calls fail
            error_response = Mock()
            error_response.raise_for_status.side_effect = Exception("503 Service Unavailable")
            mock_get.return_value = error_response
            
            # Execute fetch and expect exception
            with pytest.raises(DataAggregationError):
                scraper.fetch_rankings_page()
            
            # Verify 4 attempts made (initial + 3 retries)
            assert mock_get.call_count == 4
            
            # Verify all backoff delays executed: [1s, 2s, 4s]
            assert mock_sleep.call_count == 3
    
    def test_fetch_rankings_from_api_success(self, scraper):
        """
        Test successful fetch from FIFA API.
        """
        # Mock successful API response
        mock_api_response = {
            'rankings': [
                {
                    'rankingItem': {
                        'rank': 1,
                        'name': 'Argentina',
                        'countryCode': 'ARG',
                        'totalPoints': 1855.2,
                        'previousRank': 1,
                        'idTeam': '20001'
                    },
                    'tag': {'id': 'CONMEBOL'},
                    'previousPoints': 1850.0
                },
                {
                    'rankingItem': {
                        'rank': 2,
                        'name': 'France',
                        'countryCode': 'FRA',
                        'totalPoints': 1845.44,
                        'previousRank': 3,
                        'idTeam': '20002'
                    },
                    'tag': {'id': 'UEFA'},
                    'previousPoints': 1840.0
                }
            ]
        }
        
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_response
            mock_response.raise_for_status = Mock()
            mock_get.return_value = mock_response
            
            # Execute
            rankings = scraper.fetch_rankings_from_api('id14962')
            
            # Verify
            assert len(rankings) == 2
            
            # Verify first team (Argentina)
            argentina = rankings[0]
            assert argentina['rank'] == 1
            assert argentina['team_name'] == 'Argentina'
            assert argentina['fifa_code'] == 'ARG'
            assert argentina['confederation'] == 'CONMEBOL'
            assert argentina['points'] == 1855.2
            assert argentina['previous_rank'] == 1
            assert argentina['rank_change'] == 0  # 1 - 1 = 0
            
            # Verify second team (France)
            france = rankings[1]
            assert france['rank'] == 2
            assert france['team_name'] == 'France'
            assert france['fifa_code'] == 'FRA'
            assert france['rank_change'] == 1  # 3 - 2 = 1
    
    def test_validate_rankings_completeness(self, scraper):
        """
        Test validation of complete FIFA rankings data.
        
        FIFA has 211 member nations, so:
        - 211 teams = valid/complete
        - 200 teams = invalid/incomplete
        """
        # Test complete data (211 teams)
        complete_rankings = [{'rank': i, 'team_name': f'Team{i}'} for i in range(1, 212)]
        is_valid = scraper.validate_completeness(complete_rankings)
        assert is_valid is True
        
        # Test incomplete data (200 teams)
        incomplete_rankings = [{'rank': i, 'team_name': f'Team{i}'} for i in range(1, 201)]
        is_valid = scraper.validate_completeness(incomplete_rankings)
        assert is_valid is False
    
    def test_rate_limiting_enforced(self, scraper):
        """
        Test that 2-second minimum delay enforced between requests.
        """
        with patch('time.time') as mock_time, \
             patch('time.sleep') as mock_sleep:
            
            # Scenario 1: Only 1 second elapsed, need to sleep 1.0 more
            scraper.last_request_time = 100.0
            mock_time.return_value = 101.0  # 1 second elapsed
            
            scraper._enforce_rate_limit()
            
            # Should sleep for 1.0 second (to reach 2.0 total)
            mock_sleep.assert_called_once_with(1.0)
            mock_sleep.reset_mock()
            
            # Scenario 2: 2+ seconds elapsed, no sleep needed
            scraper.last_request_time = 100.0
            mock_time.return_value = 103.0  # 3 seconds elapsed
            
            scraper._enforce_rate_limit()
            
            # Should NOT sleep
            mock_sleep.assert_not_called()
    
    def test_scrape_and_store_success(self, scraper, mock_firestore_manager):
        """
        Test complete scrape-and-store workflow.
        """
        # Mock no cached data (force fresh fetch)
        mock_firestore_manager.get_fifa_rankings.return_value = None
        
        # Mock dependencies
        with patch.object(scraper, '_get_latest_date_id') as mock_date_id, \
             patch.object(scraper, 'fetch_rankings_from_api') as mock_api:
            
            # Mock date ID
            mock_date_id.return_value = 'id14962'
            
            # Mock API returns 211 teams
            mock_rankings = [{'rank': i, 'team_name': f'Team{i}'} for i in range(1, 212)]
            mock_api.return_value = mock_rankings
            
            # Execute scrape and store
            result = scraper.scrape_and_store()
            
            # Verify workflow executed
            mock_date_id.assert_called_once()
            mock_api.assert_called_once_with('id14962')
            
            # Verify Firestore write called
            mock_firestore_manager.update_fifa_rankings.assert_called_once()
            
            # Verify result structure
            assert result['success'] is True
            assert result['teams_scraped'] == 211
            assert isinstance(result['duration_seconds'], float)
            assert isinstance(result['fetched_at'], datetime)
            assert isinstance(result['cache_expires_at'], datetime)
            
            # Verify cache TTL (30 days)
            delta = result['cache_expires_at'] - result['fetched_at']
            assert delta.days == 30
    
    def test_cache_hit_avoids_scraping(self, scraper, mock_firestore_manager):
        """
        Test that valid cached data bypasses API fetching.
        """
        # Mock cached data (fresh, within 30 days)
        cached_data = {
            'rankings': [{'rank': 1, 'team_name': 'Argentina'}],
            'fetched_at': datetime.utcnow() - timedelta(days=10),
            'expires_at': datetime.utcnow() + timedelta(days=20),
            'total_teams': 211
        }
        
        mock_firestore_manager.get_fifa_rankings.return_value = cached_data
        
        with patch.object(scraper, '_get_latest_date_id') as mock_date_id:
            # Execute scrape and store
            result = scraper.scrape_and_store()
            
            # Verify API NOT called (cache hit)
            mock_date_id.assert_not_called()
            
            # Verify cached data returned
            assert result['success'] is True
            assert result['teams_scraped'] == 211
            assert result['cache_hit'] is True
    
    def test_force_refresh_bypasses_cache(self, scraper, mock_firestore_manager):
        """
        Test that force_refresh=True always fetches fresh data, ignoring cache.
        """
        # Mock cached data (valid)
        cached_data = {
            'rankings': [{'rank': 1, 'team_name': 'Argentina'}],
            'fetched_at': datetime.utcnow() - timedelta(days=1),
            'expires_at': datetime.utcnow() + timedelta(days=29),
            'total_teams': 211
        }
        
        mock_firestore_manager.get_fifa_rankings.return_value = cached_data
        
        with patch.object(scraper, '_get_latest_date_id') as mock_date_id, \
             patch.object(scraper, 'fetch_rankings_from_api') as mock_api:
            
            mock_date_id.return_value = 'id14962'
            mock_api.return_value = [{'rank': i, 'team_name': f'Team{i}'} for i in range(1, 212)]
            
            # Execute with force_refresh=True
            result = scraper.scrape_and_store(force_refresh=True)
            
            # Verify API WAS called (cache bypassed)
            mock_date_id.assert_called_once()
            mock_api.assert_called_once()
            
            # Verify fresh data stored
            mock_firestore_manager.update_fifa_rankings.assert_called_once()
    
    def test_get_ranking_for_team_success(self, scraper, mock_firestore_manager):
        """
        Test successful team ranking lookup by FIFA code.
        """
        # Mock Firestore document
        mock_rankings_doc = {
            'rankings': [
                {'rank': 1, 'team_name': 'Argentina', 'fifa_code': 'ARG', 'points': 1855.2},
                {'rank': 2, 'team_name': 'France', 'fifa_code': 'FRA', 'points': 1845.44},
                {'rank': 3, 'team_name': 'Brazil', 'fifa_code': 'BRA', 'points': 1837.56}
            ],
            'fetched_at': datetime.utcnow(),
            'total_teams': 211
        }
        
        mock_firestore_manager.get_fifa_rankings.return_value = mock_rankings_doc
        
        # Lookup France
        ranking = scraper.get_ranking_for_team('FRA')
        
        # Verify correct ranking returned
        assert ranking is not None
        assert ranking['rank'] == 2
        assert ranking['team_name'] == 'France'
        assert ranking['fifa_code'] == 'FRA'
        assert ranking['points'] == 1845.44
    
    def test_get_ranking_for_team_not_found(self, scraper, mock_firestore_manager):
        """
        Test team lookup for non-existent FIFA code.
        """
        # Mock Firestore document
        mock_rankings_doc = {
            'rankings': [
                {'rank': 1, 'team_name': 'Argentina', 'fifa_code': 'ARG', 'points': 1855.2},
                {'rank': 2, 'team_name': 'France', 'fifa_code': 'FRA', 'points': 1845.44}
            ],
            'fetched_at': datetime.utcnow(),
            'total_teams': 211
        }
        
        mock_firestore_manager.get_fifa_rankings.return_value = mock_rankings_doc
        
        # Lookup non-existent code
        ranking = scraper.get_ranking_for_team('ZZZ')
        
        # Verify None returned
        assert ranking is None
