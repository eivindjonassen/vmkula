# Data Model: FIFA Ranking Integration

## Overview

This document defines the data entities for FIFA world rankings scraping and storage.

---

## Entity 1: FIFA Rankings Document

**Collection**: `fifa_rankings`  
**Document ID**: `latest`  
**Purpose**: Store current FIFA world rankings for all 211 member nations

### Schema

```python
{
    "rankings": List[RankingEntry],     # Array of all team rankings
    "fetched_at": datetime,             # When data was scraped (UTC)
    "expires_at": datetime,             # Cache expiration (fetched_at + 30 days)
    "source_url": str,                  # FIFA rankings page URL
    "scraper_version": str,             # Scraper version (e.g., "1.0")
    "total_teams": int                  # Should always be 211
}
```

### RankingEntry Structure

```python
{
    "rank": int,                        # Current FIFA ranking (1-211)
    "team_name": str,                   # Official FIFA team name
    "fifa_code": str,                   # 3-letter FIFA code (e.g., "ARG")
    "confederation": str,               # Confederation (e.g., "CONMEBOL", "UEFA")
    "points": float,                    # Total FIFA ranking points
    "previous_rank": int,               # Previous ranking position
    "rank_change": int                  # Change from previous (+/-)
}
```

### Example Document

```json
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
        },
        {
            "rank": 2,
            "team_name": "France",
            "fifa_code": "FRA",
            "confederation": "UEFA",
            "points": 1835.12,
            "previous_rank": 3,
            "rank_change": 1
        }
        // ... 209 more teams
    ],
    "fetched_at": "2025-12-27T10:00:00Z",
    "expires_at": "2026-01-27T10:00:00Z",
    "source_url": "https://inside.fifa.com/fifa-world-ranking/men",
    "scraper_version": "1.0",
    "total_teams": 211
}
```

### Validation Rules

- `total_teams` MUST equal 211 (all FIFA member nations)
- `rank` values MUST be unique and sequential (1 to 211)
- `fifa_code` MUST be 3 uppercase letters
- `expires_at` MUST be `fetched_at + 30 days`
- `points` MUST be non-negative floats

---

## Entity 2: Raw Scraping Response

**Collection**: `raw_api_responses`  
**Document ID**: `fifa_rankings_2026`  
**Purpose**: Store raw HTML for audit trail and debugging

### Schema

```python
{
    "entity_type": str,                 # Always "fifa_rankings"
    "raw_response": {
        "html": str,                    # Complete raw HTML from FIFA.com
        "url": str,                     # Source URL
        "status_code": int              # HTTP status code (200, 503, etc.)
    },
    "fetched_at": datetime,             # Timestamp of scrape
    "scraper_version": str,             # Scraper version for tracking changes
    "success": bool,                    # True if scraping succeeded
    "teams_scraped": int,               # Number of teams extracted
    "duration_seconds": float,          # Time taken to scrape
    "error_message": Optional[str]      # Error details if failed
}
```

### Example Document (Success)

```json
{
    "entity_type": "fifa_rankings",
    "raw_response": {
        "html": "<!DOCTYPE html><html>...</html>",
        "url": "https://inside.fifa.com/fifa-world-ranking/men",
        "status_code": 200
    },
    "fetched_at": "2025-12-27T10:00:00Z",
    "scraper_version": "1.0",
    "success": true,
    "teams_scraped": 211,
    "duration_seconds": 12.5,
    "error_message": null
}
```

### Example Document (Failure)

```json
{
    "entity_type": "fifa_rankings",
    "raw_response": {
        "html": "",
        "url": "https://inside.fifa.com/fifa-world-ranking/men",
        "status_code": 503
    },
    "fetched_at": "2025-12-27T10:00:00Z",
    "scraper_version": "1.0",
    "success": false,
    "teams_scraped": 0,
    "duration_seconds": 5.2,
    "error_message": "HTTP 503: Service Unavailable - FIFA.com temporarily down"
}
```

---

## Entity 3: Team Stats (Modified Existing)

**Collection**: `teams`  
**Document ID**: `{team_id}`  
**Purpose**: Enrich existing team stats with FIFA ranking data

### Modified Schema (Additions Only)

```python
{
    "stats": {
        // ... existing fields (xG, form, clean_sheets, etc.)
        
        // NEW FIELDS:
        "fifa_ranking": int,            # Current FIFA rank (from rankings/latest)
        "fifa_points": float,           # FIFA ranking points
        "fifa_confederation": str,      # Team confederation (e.g., "UEFA")
        
        "fetched_at": datetime,         # Existing field
        "expires_at": datetime          # Existing field (24hr TTL)
    }
}
```

### Example Modified Document

```json
{
    "id": 15,
    "name": "Argentina",
    "fifa_code": "ARG",
    "stats": {
        "avg_xg": 2.1,
        "clean_sheets": 5,
        "form_string": "WWDWW",
        "fifa_ranking": 1,
        "fifa_points": 1837.23,
        "fifa_confederation": "CONMEBOL",
        "fetched_at": "2025-12-27T10:00:00Z",
        "expires_at": "2025-12-28T10:00:00Z"
    }
}
```

---

## Data Relationships

```
fifa_rankings/latest
    └─> rankings[] (211 teams)
            └─> fifa_code: "ARG"
                    ↓
teams/{team_id}
    └─> fifa_code: "ARG" (lookup key)
    └─> stats.fifa_ranking (enriched from rankings)

raw_api_responses/fifa_rankings_2026
    └─> audit trail for fifa_rankings/latest
```

---

## Access Patterns

### Pattern 1: Get All Rankings (Bulk Read)
```python
doc = firestore.collection("fifa_rankings").document("latest").get()
rankings = doc.to_dict()["rankings"]  # All 211 teams
```

**Cost**: 1 Firestore read

### Pattern 2: Get Specific Team Ranking
```python
doc = firestore.collection("fifa_rankings").document("latest").get()
rankings = doc.to_dict()["rankings"]
team_ranking = next((r for r in rankings if r["fifa_code"] == "ARG"), None)
```

**Cost**: 1 Firestore read + in-memory filter

### Pattern 3: Enrich Team Stats
```python
# In data_aggregator.py
fifa_data = fifa_scraper.get_ranking_for_team(team.fifa_code)
team_stats["fifa_ranking"] = fifa_data["rank"]
team_stats["fifa_points"] = fifa_data["points"]
```

**Cost**: 1 Firestore read (cached in prediction pipeline)

---

## TTL & Caching Strategy

| Data | TTL | Rationale |
|------|-----|-----------|
| `fifa_rankings/latest` | 30 days | FIFA rankings update monthly |
| `raw_api_responses/fifa_rankings_2026` | Permanent | Audit trail |
| `teams/{id}/stats` | 24 hours | Existing pattern for team stats |

---

## Document Size Estimation

**fifa_rankings/latest**:
- 211 teams × ~200 bytes/team = ~42KB
- Well under 1MB Firestore limit ✅

**raw_api_responses/fifa_rankings_2026**:
- Raw HTML: ~500KB (typical webpage size)
- Metadata: ~500 bytes
- Total: ~500KB
- Under 1MB Firestore limit ✅

---

**Data Model Version**: 1.0  
**Last Updated**: 2025-12-27  
**Status**: Ready for implementation
