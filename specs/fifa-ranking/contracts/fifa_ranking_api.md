# API Contract: FIFA Ranking Integration

## Overview

This document defines the API contracts for FIFA ranking scraping and retrieval operations.

---

## Public API Endpoints

### 1. Sync FIFA Rankings

**Endpoint**: `POST /api/sync-fifa-rankings`

**Description**: Scrapes FIFA world rankings from FIFA.com and stores them in Firestore

**Authentication**: Required (service account or admin)

**Request**:
```http
POST /api/sync-fifa-rankings HTTP/1.1
Content-Type: application/json

{
    "force_refresh": false  // Optional: bypass cache if true
}
```

**Response (Success - 200 OK)**:
```json
{
    "success": true,
    "teams_scraped": 211,
    "duration_seconds": 12.5,
    "fetched_at": "2025-12-27T10:00:00Z",
    "cache_expires_at": "2026-01-27T10:00:00Z",
    "source_url": "https://inside.fifa.com/fifa-world-ranking/men",
    "scraper_version": "1.0"
}
```

**Response (Cache Hit - 200 OK)**:
```json
{
    "success": true,
    "cache_hit": true,
    "teams_scraped": 211,
    "fetched_at": "2025-12-20T10:00:00Z",
    "cache_expires_at": "2026-01-20T10:00:00Z",
    "message": "Using cached rankings (expires in 24 days)"
}
```

**Response (Partial Success - 200 OK)**:
```json
{
    "success": true,
    "teams_scraped": 200,
    "warning": "Incomplete data: only 200 of 211 teams scraped",
    "fetched_at": "2025-12-27T10:00:00Z",
    "cache_expires_at": "2026-01-27T10:00:00Z"
}
```

**Response (Failure - 500 Internal Server Error)**:
```json
{
    "success": false,
    "error": "Failed to scrape FIFA rankings",
    "details": "HTTP 503: Service Unavailable - FIFA.com temporarily down",
    "teams_scraped": 0,
    "cached_data_available": true,
    "cached_data_age_days": 5
}
```

**Error Codes**:
- `200 OK`: Success (full or partial)
- `500 Internal Server Error`: Scraping failed
- `503 Service Unavailable`: FIFA.com unreachable after retries

---

## Internal Python Methods

### 1. FIFARankingScraper Class

#### Method: `scrape_and_store()`

```python
def scrape_and_store(self, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Scrape FIFA rankings and store in Firestore.
    
    Args:
        force_refresh: If True, bypass cache and force fresh scrape
        
    Returns:
        {
            "success": bool,
            "teams_scraped": int,
            "duration_seconds": float,
            "fetched_at": datetime,
            "cache_expires_at": datetime,
            "error_message": Optional[str]
        }
        
    Raises:
        DataAggregationError: If scraping fails after retries
    """
```

#### Method: `fetch_rankings_page()`

```python
def fetch_rankings_page(self) -> str:
    """
    Fetch raw HTML from FIFA rankings page.
    
    Returns:
        Raw HTML string
        
    Raises:
        DataAggregationError: If HTTP request fails after retries
    """
```

#### Method: `parse_rankings(html: str)`

```python
def parse_rankings(self, html: str) -> List[Dict[str, Any]]:
    """
    Parse FIFA rankings from HTML.
    
    Args:
        html: Raw HTML string from FIFA.com
        
    Returns:
        List of ranking dictionaries:
        [
            {
                "rank": int,
                "team_name": str,
                "fifa_code": str,
                "confederation": str,
                "points": float,
                "previous_rank": int,
                "rank_change": int
            },
            ...
        ]
        
    Raises:
        ValueError: If HTML cannot be parsed
    """
```

#### Method: `get_ranking_for_team(fifa_code: str)`

```python
def get_ranking_for_team(self, fifa_code: str) -> Optional[Dict[str, Any]]:
    """
    Get FIFA ranking for a specific team.
    
    Args:
        fifa_code: 3-letter FIFA country code (e.g., "ARG", "FRA")
        
    Returns:
        {
            "rank": int,
            "team_name": str,
            "fifa_code": str,
            "confederation": str,
            "points": float,
            "previous_rank": int,
            "rank_change": int
        }
        or None if team not found
    """
```

#### Method: `validate_completeness(rankings: List[Dict])`

```python
def validate_completeness(self, rankings: List[Dict[str, Any]]) -> bool:
    """
    Validate that all 211 FIFA member nations are present.
    
    Args:
        rankings: List of ranking dictionaries
        
    Returns:
        True if 211 teams present, False otherwise
    """
```

---

### 2. FirestoreManager Class (Additions)

#### Method: `get_fifa_rankings()`

```python
def get_fifa_rankings(self) -> Optional[Dict[str, Any]]:
    """
    Retrieve latest FIFA rankings from Firestore.
    
    Returns:
        {
            "rankings": List[Dict],
            "fetched_at": datetime,
            "expires_at": datetime,
            "total_teams": int,
            "source_url": str,
            "scraper_version": str
        }
        or None if not found or expired
    """
```

#### Method: `update_fifa_rankings(rankings_data, ttl_days)`

```python
def update_fifa_rankings(
    self, 
    rankings_data: Dict[str, Any], 
    ttl_days: int = 30
) -> None:
    """
    Update FIFA rankings in Firestore with TTL.
    
    Args:
        rankings_data: {
            "rankings": List[Dict],
            "source_url": str,
            "scraper_version": str,
            "total_teams": int
        }
        ttl_days: Cache TTL in days (default: 30)
        
    Side Effects:
        - Writes to fifa_rankings/latest
        - Sets fetched_at and expires_at timestamps
    """
```

#### Method: `is_fifa_rankings_cache_valid()`

```python
def is_fifa_rankings_cache_valid(self) -> bool:
    """
    Check if cached FIFA rankings are still valid (not expired).
    
    Returns:
        True if cache valid, False if expired or missing
    """
```

---

### 3. DataAggregator Class (Modifications)

#### Modified Method: `fetch_team_stats(team_id)`

```python
def fetch_team_stats(self, team_id: int, fetch_xg: bool = True) -> Dict[str, Any]:
    """
    Fetch team statistics (MODIFIED to include FIFA ranking).
    
    Args:
        team_id: Team identifier
        fetch_xg: Whether to fetch xG data from API-Football
        
    Returns:
        {
            "avg_xg": float,
            "clean_sheets": int,
            "form_string": str,
            # ... existing fields ...
            
            # NEW FIELDS:
            "fifa_ranking": int,           # FIFA rank (1-211)
            "fifa_points": float,          # FIFA points
            "fifa_confederation": str,     # Confederation
            
            "fetched_at": datetime,
            "expires_at": datetime
        }
    """
```

---

## Data Flow

```
1. POST /api/sync-fifa-rankings
   ↓
2. FIFARankingScraper.scrape_and_store()
   ↓
3. FIFARankingScraper.fetch_rankings_page()
   ↓ (HTTP GET with retry logic)
4. FIFA.com → Raw HTML
   ↓
5. FIFARankingScraper.parse_rankings(html)
   ↓ (BeautifulSoup parsing)
6. List[RankingDict] (211 teams)
   ↓
7. FirestoreManager.update_fifa_rankings(data, ttl=30)
   ↓
8. Firestore: fifa_rankings/latest (written)
   ↓
9. Response: {"success": true, "teams_scraped": 211}
```

**Prediction Pipeline Integration**:
```
1. Prediction run starts
   ↓
2. DataAggregator.fetch_team_stats(team_id)
   ↓
3. FIFARankingScraper.get_ranking_for_team(fifa_code)
   ↓
4. FirestoreManager.get_fifa_rankings() (cached)
   ↓
5. In-memory filter: find team by fifa_code
   ↓
6. Return enriched team_stats with FIFA ranking
   ↓
7. AI Agent receives FIFA ranking in prompt
```

---

## Error Handling

### Retry Strategy

All HTTP requests use exponential backoff:
```python
max_retries = 3
retry_delays = [1, 2, 4]  # seconds

Attempt 1: immediate
Attempt 2: wait 1s
Attempt 3: wait 2s  
Attempt 4: wait 4s
Then: raise DataAggregationError
```

### Graceful Degradation

If FIFA rankings unavailable:
1. Log warning
2. Return cached data (if available)
3. Continue predictions without FIFA ranking factor
4. Set `fifa_ranking: None` in team stats

### Logging

```python
# Success
logger.info(f"FIFA rankings scraped successfully: 211 teams in 12.5s")

# Partial success
logger.warning(f"Incomplete FIFA rankings: only 200/211 teams scraped")

# Cache hit
logger.info(f"Using cached FIFA rankings (expires in 24 days)")

# Failure
logger.error(f"Failed to scrape FIFA rankings: HTTP 503", exc_info=True)

# Graceful degradation
logger.warning(f"Predictions will run without FIFA ranking factor")
```

---

## Rate Limiting

```python
MIN_DELAY_SECONDS = 2.0  # Polite scraping delay

# Enforced before each HTTP request
def _enforce_rate_limit(self):
    elapsed = time.time() - self.last_request_time
    if elapsed < self.MIN_DELAY_SECONDS:
        time.sleep(self.MIN_DELAY_SECONDS - elapsed)
    self.last_request_time = time.time()
```

---

## Testing Contracts

### Mock HTTP Responses

```python
# Test fixture: mock_fifa_html
MOCK_FIFA_HTML = """
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
        <!-- ... more rows ... -->
    </table>
</html>
"""

# Usage in tests
with patch("requests.get") as mock_get:
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = MOCK_FIFA_HTML
    mock_get.return_value = mock_response
    
    scraper = FIFARankingScraper()
    rankings = scraper.scrape_and_store()
```

### Mock Firestore Responses

```python
# Mock Firestore document
mock_doc = Mock()
mock_doc.exists = True
mock_doc.to_dict.return_value = {
    "rankings": [...],
    "fetched_at": datetime.utcnow(),
    "expires_at": datetime.utcnow() + timedelta(days=30),
    "total_teams": 211
}

with patch("src.firestore_manager.firestore.Client") as mock_client:
    mock_db = MagicMock()
    mock_client.return_value = mock_db
    mock_db.collection.return_value.document.return_value.get.return_value = mock_doc
    
    manager = FirestoreManager()
    rankings = manager.get_fifa_rankings()
```

---

**Contract Version**: 1.0  
**Last Updated**: 2025-12-27  
**Status**: Ready for implementation
