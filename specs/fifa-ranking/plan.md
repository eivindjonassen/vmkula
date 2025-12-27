# Implementation Plan: fifa-ranking

**Branch**: `feature/fifa-ranking` | **Date**: 2025-12-27 | **Spec**: [spec.md](./spec.md)

---

## Planning Strategy

### Scope Assessment

- **Codebase Size**: Large (4771 source files)
- **Research Scope**: Medium - Resolved via agent-assisted research
- **Agent Assistance Recommended**: Yes - Completed

### Agent Assistance
Research delegated to @general agent for systematic codebase exploration. Key findings consolidated in [research.md](./research.md).

---

## Technical Context

- **Language/Framework**: Python 3.11+ with FastAPI
- **Primary Dependencies**: 
  - `requests>=2.31.0` (HTTP client)
  - `google-cloud-firestore>=2.11.0` (database)
  - `fastapi>=0.104.0` (web framework)
  - `pandas>=2.0.0` (data manipulation)
  - **NEW**: `beautifulsoup4>=4.12.0` (HTML parsing)
  - **NEW**: `lxml>=4.9.0` (XML/HTML parser)
- **Storage**: Firestore (migrated from SQLite)
- **Testing**: Pytest with pytest-cov (80% coverage requirement)
- **Project Type**: Web Application (backend/ + frontend/ structure)

---

## Constitution Check

### Rule 1: Python Code Style (RULES.md:9-16)
**EVIDENCE**: ✅ Compliant
- Formatter: Black (line length: 88)
- Linter: mypy for type checking
- Naming conventions: snake_case functions, PascalCase classes, UPPER_SNAKE_CASE constants
- Implementation will follow existing pattern in `data_aggregator.py` and `firestore_manager.py`

### Rule 2: TDD Requirements (RULES.md:29-45)
**EVIDENCE**: ✅ Compliant
- Tests will be written FIRST before implementation
- Pytest framework already configured (pytest.ini:1-36)
- Coverage requirement: 80% minimum (pytest.ini:18)
- Test file naming: `tests/test_fifa_ranking_scraper.py`
- Following existing test patterns from `test_data_aggregator.py` and `test_firestore_manager.py`

### Rule 3: Component Reusability (RULES.md:209-285)
**EVIDENCE**: ✅ Compliant - Reusing existing patterns
- **Rate Limiting Pattern**: Reuse from `data_aggregator.py:726-731` (modified for 2-second delay)
- **Retry Logic Pattern**: Reuse exponential backoff from `data_aggregator.py:352-424`
- **Firestore TTL Caching**: Reuse from `firestore_manager.py:169-193` (modified for 30-day TTL)
- **Diff Check Pattern**: Reuse from `firestore_publisher.py:51-93`
- **Raw Response Storage**: Reuse from `firestore_manager.py:457-497`

### Rule 4: Firestore Cost Optimization (RULES.md:268-285)
**EVIDENCE**: ✅ Compliant
- **Single Document Pattern**: Using `fifa_rankings/latest` (research.md:3 - 48× cheaper than individual documents)
- **Diff Check**: Implement before writes to avoid duplicate snapshots
- **TTL-Based Cache**: 30-day TTL (rankings update monthly)
- **Document Size**: ~42KB for 211 teams (well under 1MB Firestore limit)

### Rule 5: API Rate Limiting (RULES.md:209-219)
**EVIDENCE**: ✅ Compliant
- **Polite Scraping**: 2-second delay between requests (FIFA.com has no official rate limit but we respect their servers)
- **Exponential Backoff**: [1s, 2s, 4s] retry delays
- **User-Agent Header**: Identify bot properly
- **Aggressive Caching**: 30-day TTL to minimize requests

### Rule 6: Security Guidelines (RULES.md:310-325)
**EVIDENCE**: ✅ Compliant
- **No API Keys Required**: FIFA rankings are public data
- **Service Account Permissions**: Firestore write access already configured
- **No Secrets**: No new environment variables needed

---

## Project Structure

**Structure Decision**: Web Application (existing structure)

```
backend/
  src/
    fifa_ranking_scraper.py         # NEW: Scraper implementation
    firestore_manager.py             # MODIFY: Add FIFA ranking methods
    data_aggregator.py               # MODIFY: Enrich team stats
    main.py                          # MODIFY: Add sync endpoint
  tests/
    test_fifa_ranking_scraper.py    # NEW: Scraper tests
  requirements.txt                   # MODIFY: Add beautifulsoup4, lxml
  requirements-dev.txt               # MODIFY: Add responses (HTTP mocking)
```

---

## Phase 0: ACE-Enhanced Research & Exploration

**Status**: ✅ COMPLETE

Research delegated to @general agent. Key findings:

1. **Backend Architecture**: Python 3.11+ with FastAPI, no existing scraping libraries
2. **Storage Recommendation**: Single document pattern (`fifa_rankings/latest`) for cost efficiency
3. **Integration Point**: Enrich team stats in prediction pipeline (`data_aggregator.py`)
4. **Reusable Patterns**: Rate limiting, retry logic, TTL caching, diff check (all exist in codebase)
5. **Missing Dependencies**: BeautifulSoup4 + lxml for HTML parsing

**Output**: [research.md](./research.md) - Complete technical analysis

---

## Phase 1: Design & Contracts

### Data Model

**File**: [data-model.md](./data-model.md)

#### Entity 1: FIFA Ranking Document
```python
# Firestore Collection: fifa_rankings
# Document ID: latest
{
    "rankings": [
        {
            "rank": int,                    # Current ranking position (1-211)
            "team_name": str,               # Official FIFA team name
            "fifa_code": str,               # 3-letter FIFA code (e.g., "ARG", "BRA")
            "confederation": str,           # Confederation (e.g., "CONMEBOL", "UEFA")
            "points": float,                # Total FIFA ranking points
            "previous_rank": int,           # Previous ranking position
            "rank_change": int              # Change from previous rank (positive = up, negative = down)
        }
        # ... 210 more teams (total 211)
    ],
    "fetched_at": datetime,                 # When rankings were scraped (UTC)
    "expires_at": datetime,                 # Cache expiration (fetched_at + 30 days)
    "source_url": str,                      # FIFA rankings page URL
    "scraper_version": str,                 # Scraper version for debugging
    "total_teams": int                      # Validation: should be 211
}
```

#### Entity 2: Scraping Job Metadata
```python
# Firestore Collection: raw_api_responses
# Document ID: fifa_rankings_2026
{
    "entity_type": "fifa_rankings",
    "raw_response": {
        "html": str,                        # Raw HTML from FIFA.com
        "url": str,                         # Source URL
        "status_code": int                  # HTTP status code
    },
    "fetched_at": datetime,
    "scraper_version": str,
    "success": bool,
    "teams_scraped": int,                   # Validation: should be 211
    "duration_seconds": float,              # Scraping duration
    "error_message": Optional[str]          # If scraping failed
}
```

#### Entity 3: Team Stats Enrichment (Modified Existing)
```python
# Firestore Collection: teams
# Document ID: {team_id}
# Modified to include FIFA ranking data
{
    "stats": {
        # ... existing fields (xG, form, clean_sheets, etc.)
        "fifa_ranking": int,                # Current FIFA rank (from rankings document)
        "fifa_points": float,               # FIFA ranking points
        "fifa_confederation": str,          # Team confederation
        "fetched_at": datetime,
        "expires_at": datetime
    }
}
```

### API Contracts

**File**: `contracts/fifa_ranking_api.md`

#### Endpoint 1: Sync FIFA Rankings
```python
POST /api/sync-fifa-rankings
```

**Request**:
```json
{}  # No body required
```

**Response (Success)**:
```json
{
    "success": true,
    "teams_scraped": 211,
    "duration_seconds": 12.5,
    "fetched_at": "2025-12-27T10:00:00Z",
    "cache_expires_at": "2026-01-27T10:00:00Z",
    "source_url": "https://inside.fifa.com/fifa-world-ranking/men"
}
```

**Response (Failure)**:
```json
{
    "success": false,
    "error": "Failed to scrape FIFA rankings",
    "details": "HTTP 503: Service Unavailable",
    "teams_scraped": 0,
    "cached_data_available": true
}
```

#### Endpoint 2: Get FIFA Rankings (Internal)
```python
# Internal method in firestore_manager.py
def get_fifa_rankings() -> Optional[Dict[str, Any]]
```

**Returns**:
```python
{
    "rankings": [...],
    "fetched_at": datetime,
    "expires_at": datetime,
    "total_teams": 211
}
```

#### Endpoint 3: Get Team FIFA Ranking (Internal)
```python
# Internal method in fifa_ranking_scraper.py
def get_ranking_for_team(fifa_code: str) -> Optional[Dict[str, Any]]
```

**Returns**:
```python
{
    "rank": 5,
    "team_name": "France",
    "fifa_code": "FRA",
    "confederation": "UEFA",
    "points": 1837.23,
    "previous_rank": 4,
    "rank_change": -1
}
```

### Failing Tests

**File**: `backend/tests/test_fifa_ranking_scraper.py`

```python
"""
TDD tests for FIFA ranking scraper.
These tests will FAIL until implementation is complete.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from src.fifa_ranking_scraper import FIFARankingScraper
from src.exceptions import DataAggregationError


class TestFIFARankingScraper:
    """Test suite for FIFA ranking scraper."""

    def test_scraper_initialization(self):
        """Test scraper initializes with correct URL and config."""
        scraper = FIFARankingScraper()
        assert scraper.RANKINGS_URL == "https://inside.fifa.com/fifa-world-ranking/men"
        assert scraper.MIN_DELAY_SECONDS == 2.0
        assert scraper.CACHE_TTL_DAYS == 30

    def test_fetch_rankings_page_success(self):
        """Test successful HTTP fetch of FIFA rankings page."""
        scraper = FIFARankingScraper()
        
        with patch("requests.get") as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = "<html><body>FIFA Rankings</body></html>"
            mock_get.return_value = mock_response
            
            html = scraper.fetch_rankings_page()
            
            assert html == "<html><body>FIFA Rankings</body></html>"
            assert mock_get.call_count == 1
            # Verify User-Agent header is set
            call_args = mock_get.call_args
            assert "User-Agent" in call_args[1]["headers"]

    def test_fetch_rankings_page_retry_on_failure(self):
        """Test exponential backoff retry on HTTP errors."""
        scraper = FIFARankingScraper()
        
        with patch("requests.get") as mock_get:
            # Fail twice, succeed on third attempt
            mock_get.side_effect = [
                Mock(status_code=503, text="Service Unavailable"),
                Mock(status_code=503, text="Service Unavailable"),
                Mock(status_code=200, text="<html>Success</html>")
            ]
            
            with patch("time.sleep"):  # Don't actually sleep in tests
                html = scraper.fetch_rankings_page()
            
            assert html == "<html>Success</html>"
            assert mock_get.call_count == 3

    def test_fetch_rankings_page_max_retries_exceeded(self):
        """Test failure after max retries exceeded."""
        scraper = FIFARankingScraper()
        
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Network error")
            
            with patch("time.sleep"):
                with pytest.raises(DataAggregationError, match="Failed to fetch FIFA rankings"):
                    scraper.fetch_rankings_page()
            
            assert mock_get.call_count == 4  # Initial + 3 retries

    def test_parse_rankings_table_success(self):
        """Test parsing FIFA rankings HTML table."""
        scraper = FIFARankingScraper()
        
        # Mock HTML with realistic structure
        mock_html = """
        <html>
            <table class="rankings-table">
                <tr>
                    <td>1</td>
                    <td>Argentina</td>
                    <td>ARG</td>
                    <td>CONMEBOL</td>
                    <td>1837.23</td>
                    <td>1</td>
                </tr>
                <tr>
                    <td>2</td>
                    <td>France</td>
                    <td>FRA</td>
                    <td>UEFA</td>
                    <td>1835.12</td>
                    <td>3</td>
                </tr>
            </table>
        </html>
        """
        
        rankings = scraper.parse_rankings(mock_html)
        
        assert len(rankings) == 2
        assert rankings[0]["rank"] == 1
        assert rankings[0]["team_name"] == "Argentina"
        assert rankings[0]["fifa_code"] == "ARG"
        assert rankings[0]["confederation"] == "CONMEBOL"
        assert rankings[0]["points"] == 1837.23
        assert rankings[1]["rank"] == 2
        assert rankings[1]["rank_change"] == 1  # Moved up from 3 to 2

    def test_parse_rankings_handles_missing_data(self):
        """Test graceful handling of missing data in HTML."""
        scraper = FIFARankingScraper()
        
        # Mock HTML with incomplete data
        mock_html = """
        <html>
            <table class="rankings-table">
                <tr>
                    <td>1</td>
                    <td>Argentina</td>
                    <!-- Missing FIFA code, confederation, points -->
                </tr>
            </table>
        </html>
        """
        
        # Should not raise exception, but log warning
        rankings = scraper.parse_rankings(mock_html)
        
        # Should skip incomplete rows or use defaults
        assert isinstance(rankings, list)

    def test_scrape_and_store_success(self):
        """Test full scraping workflow with Firestore storage."""
        scraper = FIFARankingScraper()
        
        with patch.object(scraper, "fetch_rankings_page") as mock_fetch:
            with patch.object(scraper, "parse_rankings") as mock_parse:
                with patch("src.fifa_ranking_scraper.FirestoreManager") as mock_fs:
                    mock_fetch.return_value = "<html>...</html>"
                    mock_parse.return_value = [
                        {"rank": 1, "team_name": "Argentina", "fifa_code": "ARG", 
                         "confederation": "CONMEBOL", "points": 1837.23, "previous_rank": 1}
                        # ... more teams
                    ]
                    
                    result = scraper.scrape_and_store()
                    
                    assert result["success"] is True
                    assert result["teams_scraped"] == 1
                    assert "fetched_at" in result
                    assert "cache_expires_at" in result

    def test_validate_rankings_completeness(self):
        """Test validation that all 211 teams were scraped."""
        scraper = FIFARankingScraper()
        
        # Incomplete rankings (only 200 teams)
        incomplete_rankings = [{"rank": i} for i in range(1, 201)]
        
        is_valid = scraper.validate_completeness(incomplete_rankings)
        
        assert is_valid is False
        
        # Complete rankings (211 teams)
        complete_rankings = [{"rank": i} for i in range(1, 212)]
        
        is_valid = scraper.validate_completeness(complete_rankings)
        
        assert is_valid is True

    def test_rate_limiting_enforced(self):
        """Test that rate limiting delay is enforced between requests."""
        scraper = FIFARankingScraper()
        
        with patch("time.time") as mock_time:
            with patch("time.sleep") as mock_sleep:
                mock_time.side_effect = [0.0, 1.0]  # 1 second elapsed
                
                scraper._enforce_rate_limit()
                
                # Should sleep for 1 second (2.0 - 1.0 = 1.0)
                mock_sleep.assert_called_once_with(1.0)

    def test_get_ranking_for_team_success(self):
        """Test retrieving specific team ranking from cached data."""
        scraper = FIFARankingScraper()
        
        with patch("src.fifa_ranking_scraper.FirestoreManager") as mock_fs:
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                "rankings": [
                    {"rank": 1, "fifa_code": "ARG", "team_name": "Argentina", 
                     "points": 1837.23, "confederation": "CONMEBOL"},
                    {"rank": 2, "fifa_code": "FRA", "team_name": "France", 
                     "points": 1835.12, "confederation": "UEFA"}
                ]
            }
            mock_fs.return_value.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            ranking = scraper.get_ranking_for_team("FRA")
            
            assert ranking is not None
            assert ranking["rank"] == 2
            assert ranking["fifa_code"] == "FRA"
            assert ranking["points"] == 1835.12

    def test_get_ranking_for_team_not_found(self):
        """Test handling when team FIFA code not found in rankings."""
        scraper = FIFARankingScraper()
        
        with patch("src.fifa_ranking_scraper.FirestoreManager") as mock_fs:
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                "rankings": [
                    {"rank": 1, "fifa_code": "ARG", "team_name": "Argentina"}
                ]
            }
            mock_fs.return_value.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            ranking = scraper.get_ranking_for_team("ZZZ")  # Non-existent code
            
            assert ranking is None

    def test_cache_hit_avoids_scraping(self):
        """Test that cached rankings are used if not expired."""
        scraper = FIFARankingScraper()
        
        with patch("src.fifa_ranking_scraper.FirestoreManager") as mock_fs:
            # Mock cached rankings (not expired)
            mock_doc = Mock()
            mock_doc.exists = True
            mock_doc.to_dict.return_value = {
                "rankings": [...],
                "fetched_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=20)  # Still valid
            }
            mock_fs.return_value.db.collection.return_value.document.return_value.get.return_value = mock_doc
            
            with patch.object(scraper, "fetch_rankings_page") as mock_fetch:
                result = scraper.scrape_and_store(force_refresh=False)
                
                # Should NOT call fetch_rankings_page (cache hit)
                mock_fetch.assert_not_called()

    def test_force_refresh_bypasses_cache(self):
        """Test force_refresh flag bypasses cache."""
        scraper = FIFARankingScraper()
        
        with patch.object(scraper, "fetch_rankings_page") as mock_fetch:
            with patch.object(scraper, "parse_rankings") as mock_parse:
                with patch("src.fifa_ranking_scraper.FirestoreManager"):
                    mock_fetch.return_value = "<html>...</html>"
                    mock_parse.return_value = [{"rank": 1}]
                    
                    result = scraper.scrape_and_store(force_refresh=True)
                    
                    # Should call fetch even if cache valid
                    mock_fetch.assert_called_once()
```

**File**: `backend/tests/test_firestore_manager.py` (additions)

```python
# ADD to existing test_firestore_manager.py

def test_get_fifa_rankings_success(self):
    """Test retrieving FIFA rankings from Firestore."""
    with patch("src.firestore_manager.firestore.Client") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value = mock_db
        
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "rankings": [...],
            "fetched_at": datetime.utcnow(),
            "total_teams": 211
        }
        mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
        
        manager = FirestoreManager()
        rankings = manager.get_fifa_rankings()
        
        assert rankings is not None
        assert rankings["total_teams"] == 211

def test_update_fifa_rankings_with_ttl(self):
    """Test updating FIFA rankings with 30-day TTL."""
    with patch("src.firestore_manager.firestore.Client") as mock_client:
        mock_db = MagicMock()
        mock_client.return_value = mock_db
        
        manager = FirestoreManager()
        
        rankings_data = {
            "rankings": [...],
            "total_teams": 211
        }
        
        manager.update_fifa_rankings(rankings_data, ttl_days=30)
        
        # Verify set() was called with correct data including TTL
        mock_db.collection.return_value.document.return_value.set.assert_called_once()
        call_args = mock_db.collection.return_value.document.return_value.set.call_args[0][0]
        
        assert "fetched_at" in call_args
        assert "expires_at" in call_args
        assert call_args["total_teams"] == 211
```

---

## Phase 2: Task Planning Approach

The `/tasks` command will load this plan and generate a detailed, ordered task list following TDD principles:

1. **Setup Tasks**: Add dependencies to requirements.txt
2. **Test Setup**: Create test file structure
3. **Red Phase**: Write failing tests for scraper initialization
4. **Green Phase**: Implement scraper initialization
5. **Red Phase**: Write failing tests for HTTP fetching
6. **Green Phase**: Implement HTTP fetching with rate limiting
7. **Red Phase**: Write failing tests for HTML parsing
8. **Green Phase**: Implement BeautifulSoup parsing
9. **Red Phase**: Write failing tests for Firestore storage
10. **Green Phase**: Implement Firestore methods
11. **Red Phase**: Write failing tests for integration
12. **Green Phase**: Integrate with prediction pipeline
13. **Refactor**: Clean up code, optimize performance
14. **Validation**: Achieve 80% test coverage

---

## Complexity Tracking

| Violation | Justification | Alternative Rejected Because... |
|-----------|---------------|--------------------------------|
| Adding new library (BeautifulSoup4) | Required for HTML parsing - no existing scraping library in project | Using Playwright would be overkill for static HTML and add ~200MB of dependencies |

---

**Planning Status**: ✅ COMPLETE  
**Ready for Task Breakdown**: YES  
**Next Command**: `/tasks fifa-ranking`
