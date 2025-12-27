# FIFA Ranking Integration - Technical Research Report

## Executive Summary

This research examines the vmkula codebase to determine the optimal approach for implementing a FIFA world rankings scraper. Key findings:

- **Backend**: Python 3.11+ with FastAPI framework
- **No existing web scraping**: Project uses API-Football for external data; no scraping libraries present
- **Firestore primary storage**: Single document pattern preferred for frequently-read data
- **Robust testing infrastructure**: Pytest with 80% coverage requirement and TDD enforcement
- **Cloud Run deployment**: 5-minute timeout for scheduled jobs
- **Clear integration points**: Predictions pipeline already supports multiple data sources

---

## 1. Backend Architecture

### Language & Framework
- **Language**: Python 3.11+ (RULES.md:51)
- **Framework**: FastAPI (requirements.txt:5, main.py:1-1125)
- **Server**: Uvicorn with standard extensions (requirements.txt:6)
- **Testing**: Pytest with pytest-cov (requirements-dev.txt:2-3)

### Web Scraping Infrastructure
**Status**: ⚠️ **NO EXISTING SCRAPING LIBRARIES**

**Evidence**:
```python
# requirements.txt analysis
pandas>=2.0.0              # Data manipulation
google-cloud-firestore>=2.11.0
google-genai>=0.1.0
requests>=2.31.0           # HTTP client (but NO scraping libs)
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
python-dotenv>=1.0.0
```

**Current HTTP Pattern**: `requests` library for API calls only
- Used in `data_aggregator.py:298-322` for API-Football REST API
- Rate limiting via `time.sleep(0.5)` (data_aggregator.py:362)
- Exponential backoff retry logic (data_aggregator.py:353-424)

**⚠️ GAP IDENTIFIED**: Need to add scraping library (BeautifulSoup4 recommended)

**Recommendation**: 
```bash
# Add to requirements.txt
beautifulsoup4>=4.12.0    # HTML parsing
lxml>=4.9.0               # Fast XML/HTML parser
```

**Why not Selenium/Playwright?**: FIFA rankings page may be static HTML. BeautifulSoup is lightweight and sufficient for static content.

---

## 2. Data Storage Patterns

### Firestore Usage Pattern
**Primary Database**: Firestore (replaced SQLite in recent migration, MIGRATION_COMPLETE.md)

**Current Collections**:
```python
# firestore_manager.py:66-69
self.teams_collection = self.db.collection("teams")
self.matches_collection = self.db.collection("matches")
self.cities_collection = self.db.collection("host_cities")
self.raw_api_responses_collection = self.db.collection("raw_api_responses")
```

### Storage Pattern Analysis

**Pattern 1: Single Document (Hot Data)**
```python
# firestore_publisher.py:48-49
# Main snapshot: predictions/latest
doc_ref = self.db.collection("predictions").document("latest")
doc_ref.set(snapshot_with_timestamp)
```

**Pattern 2: Individual Documents (Cold Data)**
```python
# firestore_manager.py:92-121
# Individual team documents
for doc in self.teams_collection.stream():
    team_data = doc.to_dict()
```

**Pattern 3: Sub-collections (Historical Data)**
```python
# firestore_publisher.py:67-73
# Historical predictions
history_ref = (
    self.db.collection("matches")
    .document(str(match_id))
    .collection("history")
)
```

### Caching Strategy
**TTL-based caching** with Firestore metadata:
```python
# firestore_manager.py:179-193
def update_team_stats(self, team_id: int, stats: Dict, ttl_hours: int = 24):
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=ttl_hours)
    self.teams_collection.document(str(team_id)).set({
        "stats": {
            **stats,
            "fetched_at": now,
            "expires_at": expires_at,
        }
    }, merge=True)
```

### Historical Snapshots Pattern
**Diff-check before write** (cost optimization):
```python
# firestore_publisher.py:51-93
def should_save_prediction_history(self, match_id: int, new_prediction: Dict):
    """Only save if winner OR reasoning has changed."""
    latest_entry = history_ref.order_by("timestamp", desc).limit(1)
    if latest_winner != new_winner or latest_reasoning != new_reasoning:
        return True
    return False
```

---

## 3. Storage Structure Recommendation

### Analysis of Read Patterns

**Prediction Code Analysis** (main.py:634-726):
```python
# Predictions loop: Iterates through ALL teams
for match in all_matches:
    home_team = next((t for t in teams if t.id == match.home_team_id), None)
    away_team = next((t for t in teams if t.id == match.away_team_id), None)
    
    home_stats = team_stats.get(home_team.id, {})
    away_stats = team_stats.get(away_team.id, {})
    # ... generate prediction
```

**Access Pattern**: Individual lookups by team_id

### Storage Options Comparison

| Aspect | Single Document | Individual Documents |
|--------|-----------------|---------------------|
| **Collection** | `fifa_rankings/latest` | `fifa_rankings/{country_code}` |
| **Read Cost** | 1 read for all 48 teams | 48 reads (1 per team) |
| **Write Cost** | 1 write on update | 48 writes (but only if changed) |
| **Cache Complexity** | Simple (single TTL) | Complex (per-team TTL) |
| **Firestore Limit** | Max 1MB document | No limit (separate docs) |

### Cost Calculation

**Scenario**: Weekly scrape (4 times/month)

**Option 1: Single Document**
- Reads: 4 × 1 = **4 reads/month**
- Writes: 4 × 1 = **4 writes/month**
- **Total**: 8 operations/month

**Option 2: Individual Documents**
- Reads: 4 × 48 = **192 reads/month**
- Writes: 4 × 48 = **192 writes/month**
- **Total**: 384 operations/month

### RECOMMENDATION: Single Document

**Rationale**:
1. **Cost**: 48× cheaper with single document pattern
2. **Simplicity**: Single TTL, single cache invalidation
3. **Frontend Compatibility**: Already uses single document pattern (`predictions/latest`)
4. **Document Size**: 211 teams × ~200 bytes = ~42KB (well under 1MB limit)
5. **Existing Pattern**: Matches `predictions/latest` architecture

**Proposed Schema**:
```json
// fifa_rankings/latest
{
  "rankings": [
    {
      "rank": 1,
      "team_name": "Argentina",
      "fifa_code": "ARG",
      "confederation": "CONMEBOL",
      "points": 1837.23,
      "previous_rank": 1,
      "rank_change": 0
    }
    // ... 210 more teams (all 211 FIFA nations)
  ],
  "fetched_at": "2025-12-27T10:00:00Z",
  "expires_at": "2026-01-27T10:00:00Z",
  "source_url": "https://inside.fifa.com/fifa-world-ranking/men",
  "scraper_version": "1.0",
  "total_teams": 211
}
```

---

## 4. Integration Points

### Prediction Pipeline Architecture

**Current Flow** (main.py:452-969):
```
1. Load teams/matches from Firestore
2. Fetch team stats (data_aggregator) → Cache in Firestore (24hr TTL)
3. Generate AI predictions (ai_agent) → Cache with stats hash
4. Publish snapshot to predictions/latest
```

**Where FIFA Rankings Fit**:

**Recommended Approach: Enrich Team Stats**
```python
# Modify data_aggregator.py
def fetch_team_stats(self, team_id: int):
    stats = {...}  # Existing xG, form, clean sheets
    
    # NEW: Add FIFA ranking
    fifa_ranking = self.get_fifa_ranking_for_team(team.fifa_code)
    if fifa_ranking:
        stats["fifa_ranking"] = fifa_ranking["rank"]
        stats["fifa_points"] = fifa_ranking["points"]
    
    return stats
```

**AI Prompt Enhancement**:
```python
# ai_agent.py:generate_prediction()
prompt = f"""
Predict the match between {home_name} and {away_name}.

Team Statistics:
- {home_name}: 
  - Form: {home_stats['form_string']}
  - xG: {home_stats['avg_xg']}
  - FIFA Ranking: #{home_stats.get('fifa_ranking', 'N/A')}
- {away_name}:
  - Form: {away_stats['form_string']}
  - xG: {away_stats['avg_xg']}
  - FIFA Ranking: #{away_stats.get('fifa_ranking', 'N/A')}
"""
```

---

## 5. Reusable Patterns & Components

### Pattern 1: Rate-Limited HTTP Fetcher
**Location**: `data_aggregator.py:726-731`
```python
def _enforce_rate_limit(self):
    """Enforce 0.5 second delay between API requests."""
    elapsed = time.time() - self.last_request_time
    if elapsed < 0.5:
        time.sleep(0.5 - elapsed)
    self.last_request_time = time.time()
```

**Reuse**: Adapt for FIFA scraper (increase delay to 2 seconds for polite scraping)

### Pattern 2: Exponential Backoff Retry
**Location**: `data_aggregator.py:352-424`
```python
max_retries = 3
retry_delays = [1, 2, 4]

for attempt in range(max_retries + 1):
    try:
        result = self.fetch_from_api(...)
        return result
    except Exception as e:
        if attempt == max_retries:
            raise DataAggregationError(...)
        delay = retry_delays[attempt]
        time.sleep(delay)
```

**Reuse**: Copy pattern exactly for FIFA scraper

### Pattern 3: TTL-Based Firestore Caching
**Location**: `firestore_manager.py:169-193`
```python
def update_team_stats(self, team_id: int, stats: Dict, ttl_hours: int = 24):
    now = datetime.utcnow()
    expires_at = now + timedelta(hours=ttl_hours)
    self.teams_collection.document(str(team_id)).set({
        "stats": {
            **stats,
            "fetched_at": now,
            "expires_at": expires_at,
        }
    }, merge=True)
```

**Reuse**: Adapt for FIFA rankings (change TTL to 30 days)

---

## 6. Constitutional Compliance Summary

### Python Code Style (RULES.md:9-16)
- Formatter: Black (line length: 88)
- Linter: mypy for type checking
- Naming: snake_case functions, PascalCase classes, UPPER_SNAKE_CASE constants

### TDD Requirements (RULES.md:29-45)
- Write tests FIRST
- Minimum 80% coverage
- Use pytest framework

### Rate Limiting (RULES.md:209-219)
- Implement 2-second delay between requests (polite scraping)
- Exponential backoff: [1s, 2s, 4s]
- Cache aggressively (30-day TTL)

### Firestore Cost Optimization (RULES.md:268-285)
- Single document pattern for cost efficiency
- Diff check before writes
- TTL-based cache invalidation

---

## 7. Implementation Gaps & Dependencies

### Required Libraries
```bash
# Add to backend/requirements.txt
beautifulsoup4>=4.12.0    # HTML parsing
lxml>=4.9.0               # Fast XML/HTML parser

# Add to backend/requirements-dev.txt
responses>=0.24.0         # Mock HTTP responses in tests
```

### New Files to Create
```
backend/src/fifa_ranking_scraper.py           # Scraper implementation
backend/tests/test_fifa_ranking_scraper.py    # TDD tests
```

### Existing Files to Modify
```python
# backend/src/main.py - Add API endpoint
@app.post("/api/sync-fifa-rankings")
def sync_fifa_rankings() -> Dict[str, Any]:
    """Scrape and cache FIFA rankings."""
    pass

# backend/src/data_aggregator.py - Enrich team stats
def fetch_team_stats(self, team_id: int):
    # Add FIFA ranking enrichment
    pass

# backend/src/firestore_manager.py - Add FIFA ranking methods
def get_fifa_rankings(self) -> Optional[Dict[str, Any]]:
    pass

def update_fifa_rankings(self, rankings: Dict[str, Any], ttl_days: int = 30):
    pass
```

---

## 8. Key Technical Decisions

| Decision | Recommendation | Rationale |
|----------|---------------|-----------|
| **Scraping Library** | BeautifulSoup4 + lxml | Lightweight, static HTML parsing |
| **Storage Pattern** | Single document (`fifa_rankings/latest`) | 48× cheaper, simpler, matches existing pattern |
| **Cache TTL** | 30 days | FIFA rankings update monthly |
| **Scrape Schedule** | Weekly (manual initially) | Balance freshness vs. cost |
| **Integration Point** | Enrich team stats in prediction pipeline | Minimal code changes |
| **Rate Limiting** | 2 seconds between requests | Polite scraping |

---

**Report Generated**: 2025-12-27  
**Codebase Version**: Post-Firestore migration  
**Recommendation Confidence**: HIGH  
**Ready for Implementation**: ✅ YES
