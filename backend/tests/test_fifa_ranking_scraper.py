"""
Tests for FIFA World Rankings Scraper.

This module tests the FIFARankingScraper class which scrapes FIFA world rankings
from https://inside.fifa.com/fifa-world-ranking/men and stores them in Firestore.

Tests follow TDD approach: All tests in this file should FAIL initially until
the corresponding implementation is complete.

Test coverage includes:
- Scraper initialization and configuration
- HTTP fetching with retry logic and rate limiting
- HTML parsing with BeautifulSoup
- Data validation (211 teams expected)
- Firestore storage integration with TTL cache
- Team ranking lookup methods
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import time


class TestFIFARankingScraper:
    """Test suite for FIFARankingScraper class."""

    def test_scraper_initialization(self):
        """
        Test scraper initialization and configuration constants.
        
        Verifies that FIFARankingScraper is initialized with correct:
        - FIFA rankings URL
        - Minimum delay between requests (polite scraping)
        - Cache TTL (30 days for monthly updates)
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
        # Verify scraper constants
        assert scraper.RANKINGS_URL == "https://inside.fifa.com/fifa-world-ranking/men"
        assert scraper.MIN_DELAY_SECONDS == 2.0
        assert scraper.CACHE_TTL_DAYS == 30

    # T006: HTTP Fetching with Retry Logic Tests
    
    def test_fetch_rankings_page_success(self):
        """
        Test successful HTTP 200 response from FIFA rankings page.
        
        Verifies that fetch_rankings_page():
        - Makes HTTP GET request to FIFA rankings URL
        - Sets User-Agent header
        - Returns HTML content on success
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
        # Mock successful HTTP response
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html><body>FIFA Rankings</body></html>"
            mock_get.return_value = mock_response
            
            # Execute fetch
            html = scraper.fetch_rankings_page()
            
            # Verify request made with correct URL
            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert scraper.RANKINGS_URL in str(call_args)
            
            # Verify User-Agent header set
            headers = call_args[1].get('headers', {})
            assert 'User-Agent' in headers
            
            # Verify HTML returned
            assert html == "<html><body>FIFA Rankings</body></html>"
    
    def test_fetch_rankings_page_retry_on_failure(self):
        """
        Test retry logic with exponential backoff on transient failures.
        
        Simulates 503 Service Unavailable errors on first 2 attempts,
        then succeeds on 3rd attempt.
        
        Verifies:
        - Exponential backoff delays: [1s, 2s]
        - Success on 3rd attempt (after 2 retries)
        - Total of 3 HTTP calls made
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        from src.exceptions import DataAggregationError
        
        scraper = FIFARankingScraper()
        
        # Mock responses: fail twice, then succeed
        with patch('requests.get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # First two calls raise 503 errors
            error_response_1 = Mock()
            error_response_1.status_code = 503
            error_response_1.raise_for_status.side_effect = Exception("503 Service Unavailable")
            
            error_response_2 = Mock()
            error_response_2.status_code = 503
            error_response_2.raise_for_status.side_effect = Exception("503 Service Unavailable")
            
            # Third call succeeds
            success_response = Mock()
            success_response.status_code = 200
            success_response.text = "<html>Rankings</html>"
            
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
    
    def test_fetch_rankings_page_max_retries_exceeded(self):
        """
        Test that DataAggregationError raised after max retries exceeded.
        
        Simulates persistent failures (4 attempts total: initial + 3 retries).
        
        Verifies:
        - All retry delays executed: [1s, 2s, 4s]
        - DataAggregationError raised after 4 attempts
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        from src.exceptions import DataAggregationError
        
        scraper = FIFARankingScraper()
        
        # Mock persistent failures
        with patch('requests.get') as mock_get, \
             patch('time.sleep') as mock_sleep:
            
            # All calls fail with 503
            error_response = Mock()
            error_response.status_code = 503
            error_response.raise_for_status.side_effect = Exception("503 Service Unavailable")
            
            mock_get.return_value = error_response
            
            # Execute fetch and expect exception
            with pytest.raises(DataAggregationError):
                scraper.fetch_rankings_page()
            
            # Verify 4 attempts made (initial + 3 retries)
            assert mock_get.call_count == 4
            
            # Verify all backoff delays executed: [1s, 2s, 4s]
            assert mock_sleep.call_count == 3
            mock_sleep.assert_any_call(1)
            mock_sleep.assert_any_call(2)
            mock_sleep.assert_any_call(4)
    
    # T007: HTML Parsing Tests
    
    def test_parse_rankings_table_success(self):
        """
        Test successful parsing of FIFA rankings HTML table.
        
        Parses mock HTML with 2 teams and verifies returned structure:
        - List of dicts with rank, team_name, fifa_code, confederation, points, previous_rank, rank_change
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
        # Mock FIFA.com HTML table structure
        mock_html = """
        <html>
        <body>
            <table class="table">
                <tbody>
                    <tr>
                        <td class="rank">1</td>
                        <td class="team-name">Argentina</td>
                        <td class="fifa-code">ARG</td>
                        <td class="confederation">CONMEBOL</td>
                        <td class="points">1855.2</td>
                        <td class="previous-rank">1</td>
                        <td class="rank-change">0</td>
                    </tr>
                    <tr>
                        <td class="rank">2</td>
                        <td class="team-name">France</td>
                        <td class="fifa-code">FRA</td>
                        <td class="confederation">UEFA</td>
                        <td class="points">1845.44</td>
                        <td class="previous-rank">3</td>
                        <td class="rank-change">+1</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        
        # Execute parsing
        rankings = scraper.parse_rankings(mock_html)
        
        # Verify list of dicts returned
        assert isinstance(rankings, list)
        assert len(rankings) == 2
        
        # Verify first team (Argentina)
        argentina = rankings[0]
        assert argentina['rank'] == 1
        assert argentina['team_name'] == 'Argentina'
        assert argentina['fifa_code'] == 'ARG'
        assert argentina['confederation'] == 'CONMEBOL'
        assert argentina['points'] == 1855.2
        assert argentina['previous_rank'] == 1
        assert argentina['rank_change'] == 0
        
        # Verify second team (France)
        france = rankings[1]
        assert france['rank'] == 2
        assert france['team_name'] == 'France'
        assert france['fifa_code'] == 'FRA'
        assert france['confederation'] == 'UEFA'
        assert france['points'] == 1845.44
        assert france['previous_rank'] == 3
        assert france['rank_change'] == 1
    
    def test_parse_rankings_handles_missing_data(self):
        """
        Test graceful handling of incomplete HTML data.
        
        Parses HTML with missing fields and verifies:
        - Parser doesn't crash
        - Missing fields set to None or default values
        - Valid data still extracted
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
        # Mock incomplete HTML (missing rank_change and previous_rank)
        mock_html = """
        <html>
        <body>
            <table class="table">
                <tbody>
                    <tr>
                        <td class="rank">1</td>
                        <td class="team-name">Brazil</td>
                        <td class="fifa-code">BRA</td>
                        <td class="confederation">CONMEBOL</td>
                        <td class="points">1837.56</td>
                    </tr>
                </tbody>
            </table>
        </body>
        </html>
        """
        
        # Execute parsing - should not crash
        rankings = scraper.parse_rankings(mock_html)
        
        # Verify parsing succeeded
        assert isinstance(rankings, list)
        assert len(rankings) == 1
        
        # Verify valid data extracted
        brazil = rankings[0]
        assert brazil['rank'] == 1
        assert brazil['team_name'] == 'Brazil'
        assert brazil['fifa_code'] == 'BRA'
        assert brazil['confederation'] == 'CONMEBOL'
        assert brazil['points'] == 1837.56
        
        # Verify missing fields handled gracefully (None or default)
        assert brazil.get('previous_rank') in (None, 0)
        assert brazil.get('rank_change') in (None, 0)
    
    # T008: Rankings Validation Tests
    
    def test_validate_rankings_completeness(self):
        """
        Test validation of complete FIFA rankings data.
        
        FIFA has 211 member nations, so:
        - 211 teams = valid/complete
        - 200 teams = invalid/incomplete
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
        # Test complete data (211 teams)
        complete_rankings = [{'rank': i, 'team_name': f'Team{i}'} for i in range(1, 212)]
        is_valid = scraper.validate_completeness(complete_rankings)
        assert is_valid is True
        
        # Test incomplete data (200 teams)
        incomplete_rankings = [{'rank': i, 'team_name': f'Team{i}'} for i in range(1, 201)]
        is_valid = scraper.validate_completeness(incomplete_rankings)
        assert is_valid is False
    
    # T009: Rate Limiting Tests
    
    def test_rate_limiting_enforced(self):
        """
        Test that 2-second minimum delay enforced between requests.
        
        Scenarios:
        - If 1 second elapsed: sleep(1.0) to reach 2.0 total
        - If 2+ seconds elapsed: no sleep needed
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
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
    
    # T010: Firestore Storage Integration Tests
    
    def test_scrape_and_store_success(self):
        """
        Test complete scrape-and-store workflow.
        
        Mocks:
        - fetch_rankings_page() returns HTML
        - parse_rankings() returns 211 teams
        - Firestore write succeeds
        
        Verifies returned dict contains:
        - success: True
        - teams_scraped: 211
        - duration_seconds: float
        - fetched_at: datetime
        - cache_expires_at: datetime (fetched_at + 30 days)
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
        # Mock dependencies
        with patch.object(scraper, 'fetch_rankings_page') as mock_fetch, \
             patch.object(scraper, 'parse_rankings') as mock_parse, \
             patch('src.firestore_manager.FirestoreManager') as mock_fm:
            
            # Mock fetch returns HTML
            mock_fetch.return_value = "<html>Rankings</html>"
            
            # Mock parse returns 211 teams
            mock_rankings = [{'rank': i, 'team_name': f'Team{i}'} for i in range(1, 212)]
            mock_parse.return_value = mock_rankings
            
            # Mock Firestore manager
            mock_manager = Mock()
            mock_fm.return_value = mock_manager
            
            # Execute scrape and store
            result = scraper.scrape_and_store()
            
            # Verify fetch called
            mock_fetch.assert_called_once()
            
            # Verify parse called with HTML
            mock_parse.assert_called_once_with("<html>Rankings</html>")
            
            # Verify Firestore write called
            mock_manager.update_fifa_rankings.assert_called_once()
            
            # Verify result structure
            assert result['success'] is True
            assert result['teams_scraped'] == 211
            assert isinstance(result['duration_seconds'], float)
            assert isinstance(result['fetched_at'], datetime)
            assert isinstance(result['cache_expires_at'], datetime)
            
            # Verify cache TTL (30 days)
            delta = result['cache_expires_at'] - result['fetched_at']
            assert delta.days == 30
    
    def test_cache_hit_avoids_scraping(self):
        """
        Test that valid cached data bypasses HTTP scraping.
        
        Mocks:
        - Firestore has cached rankings less than 30 days old
        
        Verifies:
        - fetch_rankings_page() NOT called
        - Cached data returned directly
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
        # Mock cached data (fresh, within 30 days)
        cached_data = {
            'rankings': [{'rank': 1, 'team_name': 'Argentina'}],
            'fetched_at': datetime.utcnow() - timedelta(days=10),
            'expires_at': datetime.utcnow() + timedelta(days=20),
            'total_teams': 211
        }
        
        with patch.object(scraper, 'fetch_rankings_page') as mock_fetch, \
             patch('src.firestore_manager.FirestoreManager') as mock_fm:
            
            # Mock Firestore returns cached data
            mock_manager = Mock()
            mock_manager.get_fifa_rankings.return_value = cached_data
            mock_fm.return_value = mock_manager
            
            # Execute scrape and store
            result = scraper.scrape_and_store()
            
            # Verify fetch NOT called (cache hit)
            mock_fetch.assert_not_called()
            
            # Verify cached data returned
            assert result['success'] is True
            assert result['teams_scraped'] == 211
            assert result['cache_hit'] is True
    
    def test_force_refresh_bypasses_cache(self):
        """
        Test that force_refresh=True always scrapes, ignoring cache.
        
        Verifies:
        - fetch_rankings_page() IS called even with valid cache
        - Fresh data stored to Firestore
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
        # Mock cached data (valid)
        cached_data = {
            'rankings': [{'rank': 1, 'team_name': 'Argentina'}],
            'fetched_at': datetime.utcnow() - timedelta(days=1),
            'expires_at': datetime.utcnow() + timedelta(days=29),
            'total_teams': 211
        }
        
        with patch.object(scraper, 'fetch_rankings_page') as mock_fetch, \
             patch.object(scraper, 'parse_rankings') as mock_parse, \
             patch('src.firestore_manager.FirestoreManager') as mock_fm:
            
            # Mock Firestore returns cached data
            mock_manager = Mock()
            mock_manager.get_fifa_rankings.return_value = cached_data
            mock_fm.return_value = mock_manager
            
            # Mock fresh scrape
            mock_fetch.return_value = "<html>New Rankings</html>"
            mock_parse.return_value = [{'rank': i, 'team_name': f'Team{i}'} for i in range(1, 212)]
            
            # Execute with force_refresh=True
            result = scraper.scrape_and_store(force_refresh=True)
            
            # Verify fetch WAS called (cache bypassed)
            mock_fetch.assert_called_once()
            mock_parse.assert_called_once()
            
            # Verify fresh data stored
            mock_manager.update_fifa_rankings.assert_called_once()
    
    # T011: Team Ranking Lookup Tests
    
    def test_get_ranking_for_team_success(self):
        """
        Test successful team ranking lookup by FIFA code.
        
        Mocks Firestore document with rankings data, looks up "FRA".
        
        Verifies:
        - Correct ranking data returned for France
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
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
        
        with patch('src.firestore_manager.FirestoreManager') as mock_fm:
            # Mock Firestore manager
            mock_manager = Mock()
            mock_manager.get_fifa_rankings.return_value = mock_rankings_doc
            mock_fm.return_value = mock_manager
            
            # Lookup France
            ranking = scraper.get_ranking_for_team('FRA')
            
            # Verify correct ranking returned
            assert ranking is not None
            assert ranking['rank'] == 2
            assert ranking['team_name'] == 'France'
            assert ranking['fifa_code'] == 'FRA'
            assert ranking['points'] == 1845.44
    
    def test_get_ranking_for_team_not_found(self):
        """
        Test team lookup for non-existent FIFA code.
        
        Looks up "ZZZ" (non-existent) and verifies None returned.
        
        Expected to FAIL until implementation in T013.
        """
        from src.fifa_ranking_scraper import FIFARankingScraper
        
        scraper = FIFARankingScraper()
        
        # Mock Firestore document
        mock_rankings_doc = {
            'rankings': [
                {'rank': 1, 'team_name': 'Argentina', 'fifa_code': 'ARG', 'points': 1855.2},
                {'rank': 2, 'team_name': 'France', 'fifa_code': 'FRA', 'points': 1845.44}
            ],
            'fetched_at': datetime.utcnow(),
            'total_teams': 211
        }
        
        with patch('src.firestore_manager.FirestoreManager') as mock_fm:
            # Mock Firestore manager
            mock_manager = Mock()
            mock_manager.get_fifa_rankings.return_value = mock_rankings_doc
            mock_fm.return_value = mock_manager
            
            # Lookup non-existent code
            ranking = scraper.get_ranking_for_team('ZZZ')
            
            # Verify None returned
            assert ranking is None
