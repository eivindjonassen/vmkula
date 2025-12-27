# Research Findings: API-Football Data Refactor

**Date**: 2025-12-27  
**Researcher**: OpenCode AI  
**Objective**: Document current architecture to inform SQLite elimination and API-Football migration strategy

---

## Executive Summary

The codebase has **already migrated from SQLite to Firestore** as the primary database. However, there are **legacy references and migration scripts** that still mention SQLite and a deprecated `db_manager.py` module. The current architecture uses:

1. **Firestore** as the single source of truth for teams, matches, and predictions
2. **API-Football** as the external data source for team statistics
3. **Smart caching** with TTL and hash-based invalidation
4. **No active SQLite dependencies** (migration completed, but scripts remain)

**Critical Finding**: The migration from SQLite to Firestore has already been completed. The refactor goal should shift from "eliminate SQLite" to "clean up legacy migration code and optimize API-Football integration."

---

## 1. Current Data Flow Architecture

### Primary Data Flow (Active)

```
API-Football v3
     ↓
data_aggregator.py (fetch team stats, cache locally)
     ↓
firestore_manager.py (cache team stats in Firestore with 24h TTL)
     ↓
main.py (fetch cached stats, generate predictions)
     ↓
ai_agent.py (Gemini predictions)
     ↓
firestore_publisher.py (publish predictions/latest)
     ↓
Frontend (fetch predictions/latest)
```

### Data Sources

| Source | Purpose | Files |
|--------|---------|-------|
| **Firestore** | Primary database (teams, matches, predictions) | `firestore_manager.py` |
| **API-Football v3** | Team statistics (xG, form, clean sheets) | `data_aggregator.py` |
| **Gemini AI** | Match predictions | `ai_agent.py` |
| **Local file cache** | API-Football response caching (24h TTL) | `data_aggregator.py` (lines 49, 214-256) |

### Key Files and Responsibilities

#### `firestore_manager.py` (465 lines)
- **Primary database interface** for Firestore
- Manages `teams`, `matches`, `host_cities` collections
- Implements smart caching with TTL (24-hour default)
- Hash-based change detection for predictions (lines 433-464)
- **No SQLite imports** ✅

**Key Methods**:
- `get_all_teams()` - Fetch all teams from Firestore (lines 91-107)
- `get_all_matches()` - Fetch all matches from Firestore (lines 227-243)
- `update_team_stats()` - Cache team stats with TTL (lines 149-174)
- `should_regenerate_prediction()` - Hash-based cache invalidation (lines 338-368)

#### `data_aggregator.py` (732 lines)
- **API-Football integration** for team statistics
- Fetches fixtures, statistics, and predictions from API-Football v3
- Implements rate limiting (0.5s between requests, line 362)
- Exponential backoff retry logic (1s, 2s, 4s - lines 352-421)
- Local file-based caching (24h TTL, lines 202-256)
- **No SQLite imports** ✅

**API-Football Endpoints Used**:
- `GET /fixtures` - Team fixtures (line 278)
- `GET /fixtures/statistics` - Match statistics (xG) (line 662)
- `GET /predictions` - API-Football predictions (line 606)

**Key Methods**:
- `fetch_team_stats()` - Main entry point for stats (lines 324-424)
- `transform_api_response()` - Parse API-Football fixtures (lines 59-145)
- `compute_metrics()` - Calculate team statistics (lines 147-200)
- `fetch_match_prediction()` - Get API-Football predictions (lines 578-631)

#### `main.py` (1035 lines)
- **FastAPI application** with prediction pipeline endpoints
- Uses `firestore_manager.py` for all data operations
- **Comments reference old `DBManager`** (lines 167, 190, 193) but does NOT import it ✅
- Two main endpoints:
  - `POST /api/update-tournament` - Load tournament structure (lines 126-441)
  - `POST /api/update-predictions` - Generate AI predictions (lines 444-961)

**Data Flow in Prediction Pipeline** (lines 444-961):
1. Load teams/matches from Firestore (lines 472-516)
2. Fetch team stats with Firestore caching (lines 518-602)
3. Generate AI predictions with hash-based caching (lines 603-737)
4. Publish to `predictions/latest` (lines 738-928)

#### `firestore_publisher.py` (122 lines)
- Publishes tournament snapshots to `predictions/latest` document
- Implements diff-based history tracking (lines 51-93)
- **No SQLite imports** ✅

---

## 2. SQLite Dependencies

### SQLite Import Search Results

**Only 1 file imports sqlite3**:
- `backend/migrate_to_firestore.py` (line 20) - **Migration script only**

### References to `db_manager.py` or `DBManager`

| File | Line | Type | Status |
|------|------|------|--------|
| `populate_from_api_football.py` | 28 | import | **⚠️ Legacy migration script** |
| `migrate_to_firestore.py` | 23 | import | **⚠️ Legacy migration script** |
| `test_norway_integration.py` | 19 | import | **⚠️ Test file (likely deprecated)** |
| `main.py` | 167, 190, 193 | comment | **Documentation comments only** |
| Documentation files | Various | reference | **Documentation only** |

### SQLite Database Files

**No `.db` files found** in the backend directory (verified with `find` command).

### Critical Assessment

✅ **SQLite has already been eliminated from production code**  
⚠️ **Legacy migration scripts remain** (`migrate_to_firestore.py`, `populate_from_api_football.py`)  
⚠️ **`db_manager.py` file is missing** - referenced by migration scripts but doesn't exist  
✅ **Main application (`main.py`) uses only Firestore** - comments are legacy documentation

---

## 3. API-Football Integration Points

### Current API-Football Endpoints

| Endpoint | Purpose | File:Line | Rate Limit Handling |
|----------|---------|-----------|---------------------|
| `GET /fixtures` | Team fixtures (last 5 matches) | `data_aggregator.py:278` | 0.5s delay + retry |
| `GET /fixtures/statistics` | Match statistics (xG) | `data_aggregator.py:662` | 0.5s delay + retry |
| `GET /predictions` | API-Football predictions | `data_aggregator.py:606` | 0.5s delay + retry |

### API-Football Team ID Mappings

**Stored in**: `populate_from_api_football.py` (lines 39-103)

**Mapping Format**:
```python
API_FOOTBALL_TEAM_IDS = {
    "MEX": 16,   # Mexico
    "USA": 2384, # United States
    "FRA": 2,    # France
    # ... 48+ teams
}
```

**Storage Location**: 
- **Firestore `teams` collection** - Each team document has `api_football_id` field (line 141 in `firestore_manager.py`)
- **Migration script** applies these mappings to Firestore (lines 146-201 in `populate_from_api_football.py`)

### API-Football Request/Response Flow

**Request Headers** (`data_aggregator.py:280-284`):
```python
headers = {
    "x-rapidapi-key": config.API_FOOTBALL_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io",
}
```

**Response Format** (API-Football v3):
```json
{
  "response": [
    {
      "fixture": { "id": 123, "date": "2024-01-01" },
      "teams": {
        "home": { "id": 1, "name": "Team A" },
        "away": { "id": 2, "name": "Team B" }
      },
      "goals": { "home": 2, "away": 1 }
    }
  ]
}
```

**Transformation** (`data_aggregator.py:59-145`):
1. Parse raw API response
2. Determine team perspective (home/away)
3. Extract goals, result (W/D/L)
4. Optionally fetch xG from `/fixtures/statistics` endpoint
5. Return internal fixture format

**Metrics Computation** (`data_aggregator.py:147-200`):
```python
TeamStatistics(
    avg_xg: Optional[float],
    clean_sheets: int,
    form_string: str,  # "W-W-D-L-W"
    data_completeness: float,  # 0.0-1.0
    confidence: str,  # "high", "medium", "low"
    fallback_mode: Optional[str]
)
```

### Caching Strategy

**Two-layer caching**:

1. **Local file cache** (`data_aggregator.py:202-256`):
   - Location: `backend/cache/team_stats_{team_id}_{YYYY-MM-DD}.json`
   - TTL: 24 hours (date-based expiration)
   - Purpose: Reduce API-Football calls

2. **Firestore cache** (`firestore_manager.py:149-174`):
   - Collection: Embedded in `teams` collection (`stats` field)
   - TTL: 24 hours (configurable via `ttl_hours` parameter)
   - Metadata: `fetched_at`, `expires_at` timestamps
   - Purpose: Share cache across multiple backend instances

---

## 4. Firestore Schema & Collections

### Collections

| Collection | Purpose | Document ID | Key Fields |
|------------|---------|-------------|------------|
| `teams` | Tournament teams | `{team_id}` (e.g., "1") | `id`, `name`, `fifa_code`, `group`, `api_football_id`, `stats` |
| `matches` | Tournament matches | `{match_id}` (e.g., "1") | `id`, `match_number`, `home_team_id`, `away_team_id`, `venue`, `stage_id`, `prediction` |
| `host_cities` | Host cities/venues | `{city_id}` (e.g., "1") | `id`, `city_name`, `country`, `venue_name` |
| `predictions` | Published snapshots | `latest` | `groups`, `matches`, `bracket`, `predictions`, `updated_at` |

### Document Structures

#### `teams/{team_id}`
```json
{
  "id": 1,
  "name": "Mexico",
  "fifa_code": "MEX",
  "group": "A",
  "api_football_id": 16,
  "is_placeholder": false,
  "stats": {
    "avg_xg": 1.8,
    "clean_sheets": 3,
    "form_string": "W-W-D-W-L",
    "data_completeness": 1.0,
    "confidence": "high",
    "has_real_data": true,
    "fetched_at": "2026-06-11T10:00:00Z",
    "expires_at": "2026-06-12T10:00:00Z"
  }
}
```

#### `matches/{match_id}`
```json
{
  "id": 1,
  "match_number": 1,
  "home_team_id": 1,
  "away_team_id": 2,
  "home_team_name": "Mexico",
  "away_team_name": "Poland",
  "city": "New Jersey",
  "venue": "MetLife Stadium",
  "stage_id": 1,
  "kickoff": "2026-06-12T15:00:00Z",
  "label": "Mexico vs Poland",
  "api_football_fixture_id": null,
  "has_real_data": false,
  "prediction": {
    "winner": "Mexico",
    "win_probability": 65,
    "predicted_home_score": 2,
    "predicted_away_score": 1,
    "reasoning": "Mexico's avg xG of 1.8 vs Poland's 1.2...",
    "confidence": "high",
    "generated_at": "2026-06-11T10:00:00Z",
    "team_stats_hash": "a1b2c3d4"
  }
}
```

#### `predictions/latest`
```json
{
  "groups": {
    "A": [
      {
        "team_name": "Mexico",
        "rank": 1,
        "points": 7,
        "played": 3,
        "won": 2,
        "draw": 1,
        "lost": 0,
        "goals_for": 5,
        "goals_against": 1,
        "goal_difference": 4,
        "has_real_data": true,
        "predicted_rank": 1
      }
    ]
  },
  "matches": [ /* all 104 matches */ ],
  "bracket": [ /* knockout matches */ ],
  "predictions": [ /* AI predictions */ ],
  "ai_summary": "Tournament structure loaded...",
  "favorites": ["Brazil", "France", "Argentina"],
  "darkHorses": ["Mexico", "Japan", "Senegal"],
  "updated_at": "2026-06-11T10:00:00Z"
}
```

### Caching Implementation

#### Team Stats Cache
- **Location**: `teams/{team_id}/stats` (embedded field)
- **TTL**: 24 hours (lines 149-174 in `firestore_manager.py`)
- **Invalidation**: Time-based expiration (`expires_at` timestamp)
- **Cache Check**: `get_team_stats()` method (lines 176-204)

#### Prediction Cache
- **Location**: `matches/{match_id}/prediction` (embedded field)
- **TTL**: Indefinite (invalidated on stats change)
- **Invalidation**: Hash-based change detection (lines 338-368)
- **Cache Check**: `should_regenerate_prediction()` method

**Hash Calculation** (`firestore_manager.py:433-464`):
```python
def calculate_stats_hash(*stats_dicts):
    # Extract only prediction-relevant fields
    relevant_data = []
    for stats in stats_dicts:
        relevant = {
            "form_string": stats.get("form_string"),
            "clean_sheets": stats.get("clean_sheets"),
            "avg_xg": stats.get("avg_xg"),
        }
        relevant_data.append(str(sorted(relevant.items())))
    
    combined = "|".join(relevant_data)
    return hashlib.md5(combined.encode()).hexdigest()
```

### Firestore Security Rules

**Location**: `firestore.rules` (project root)

**Expected Rules** (not read in this research, but documented):
- Public read access to `predictions/latest`
- Admin-only write access to all collections
- Optional: Read access to `teams` and `matches` collections

---

## 5. Backward Compatibility Requirements

### Frontend Dependencies

**Frontend Firestore Client**: `frontend/lib/firestore.ts` (373 lines)

**Expected Document Structure** (lines 138-146):
```typescript
const data: TournamentSnapshot = {
  groups: transformGroups(rawData.groups || {}),
  matches: transformMatches(rawData.matches || [], predictionsMap),
  bracket: transformMatches(rawData.bracket || [], predictionsMap),
  aiSummary: rawData.ai_summary || '',
  favorites: rawData.favorites || [],
  darkHorses: rawData.darkHorses || rawData.dark_horses || [],
  updatedAt: rawData.updated_at || rawData.updatedAt || new Date().toISOString(),
}
```

### Field Name Mapping

**Critical**: Frontend expects **snake_case** from Firestore, transforms to **camelCase** internally.

| Firestore Field | Frontend Field | Notes |
|-----------------|----------------|-------|
| `match_number` | `matchNumber` | Required |
| `home_team_id` | `homeTeamId` | Required |
| `away_team_id` | `awayTeamId` | Required |
| `home_team_name` | `homeTeamName` | Required |
| `away_team_name` | `awayTeamName` | Required |
| `stage_id` | `stageId` | Required |
| `has_real_data` | `hasRealData` | Required for data quality indicators |
| `ai_summary` | `aiSummary` | Required |
| `updated_at` | `updatedAt` | Required (fallback to `updatedAt`) |

### Breaking Change Risk

**Low Risk** ✅ - Backend already uses snake_case Firestore schema, frontend transforms to camelCase.

**Potential Issues**:
1. Adding new fields → Must update `transformMatches()` and `transformGroups()` in `firestore.ts`
2. Removing fields → Frontend may show `undefined`, need graceful degradation
3. Changing field types → Could break frontend parsing

---

## 6. Testing Infrastructure

### Existing Test Files

| Test File | Purpose | Status |
|-----------|---------|--------|
| `test_ai_agent.py` | AI prediction generation | ✅ Active |
| `test_config.py` | Configuration management | ✅ Active |
| `test_data_aggregator.py` | API-Football integration | ✅ Active |
| `test_fifa_engine.py` | Tournament logic (standings, bracket) | ✅ Active |
| `test_firestore_publisher.py` | Firestore publishing | ✅ Active |
| `test_norway_integration.py` | Norway data integration | ⚠️ References `DBManager` (deprecated) |

### Test Coverage for Data Operations

**Firestore Operations**:
- ✅ Team CRUD operations
- ✅ Match CRUD operations
- ✅ Prediction caching with hash validation
- ✅ Publishing snapshots to `predictions/latest`

**API-Football Operations**:
- ✅ Fixture fetching and parsing
- ✅ Team statistics calculation
- ✅ Rate limiting and retry logic
- ✅ Fallback mode for missing xG data

**SQLite Operations**:
- ❌ No test coverage (SQLite eliminated)
- ⚠️ `test_norway_integration.py` imports `DBManager` (deprecated)

### Test Gaps

1. **No integration tests** for end-to-end prediction pipeline
2. **No tests** for Firestore cache invalidation edge cases
3. **No performance tests** for 104-match prediction generation
4. **No tests** for frontend Firestore schema compatibility

---

## Critical Findings

### 1. Migration Already Complete ✅

**Evidence**:
- Main application (`main.py`) uses only Firestore
- No SQLite database files exist in the backend
- `firestore_manager.py` is the primary database interface
- Frontend expects Firestore document structure

**Implication**: The refactor goal is **NOT** "migrate from SQLite" but rather "clean up legacy migration artifacts."

### 2. API-Football as Single Source of Truth ⚠️

**Current Reality**: API-Football is **NOT** the single source of truth:
- **Teams and matches** are stored in Firestore (static tournament structure)
- **Team statistics** are fetched from API-Football and cached in Firestore
- **Match predictions** are generated by Gemini AI, not API-Football

**Clarification Needed**:
- What does "API-Football as single source of truth" mean?
- Option A: Fetch tournament structure (teams, fixtures) from API-Football instead of hardcoding in Firestore
- Option B: Keep tournament structure in Firestore, only fetch statistics from API-Football (current state)

### 3. Legacy Migration Code Still Exists ⚠️

**Files to Clean Up**:
- `backend/migrate_to_firestore.py` - One-time migration script
- `backend/populate_from_api_football.py` - Includes migration logic
- `backend/test_norway_integration.py` - References deprecated `DBManager`
- Documentation comments in `main.py` (lines 167, 190, 193)

### 4. Missing `db_manager.py` File ❌

**Issue**: Migration scripts import `src.db_manager`, but the file doesn't exist in `backend/src/`.

**Possible Explanations**:
1. File was deleted after migration
2. File exists elsewhere (not in scanned files)
3. Scripts are broken (never ran after migration)

**Recommendation**: Delete migration scripts or move to `backend/archive/` directory.

### 5. Dual Caching Strategy 🔍

**Current Implementation**:
1. Local file cache (24h TTL, date-based)
2. Firestore cache (24h TTL, timestamp-based)

**Potential Issue**: Cache inconsistency if multiple backend instances write to local file cache but read from Firestore.

**Recommendation**: Eliminate local file cache, use only Firestore cache for multi-instance consistency.

---

## Recommendations for Refactor Approach

### ✅ SELECTED APPROACH: Option A+ (API-Football Source of Truth with Sync)

**Goal**: Clean up legacy code AND establish API-Football as canonical data source with change detection.

**Architecture**:
```
API-Football v3 (Source of Truth)
     ↓
api_football_raw collection (Raw API responses, timestamped)
     ↓
Sync Process (Change Detection)
     ↓
teams/matches collections (Normalized internal structure)
     ↓
Prediction Pipeline (Existing flow)
```

**New Firestore Collections**:

1. **`api_football_raw`** collection:
   - Purpose: Store raw API-Football responses as documents
   - Document structure:
   ```json
   {
     "type": "team_stats" | "fixtures" | "predictions",
     "team_id": 16,  // API-Football team ID
     "data": { /* raw API response */ },
     "fetched_at": "2026-06-11T10:00:00Z",
     "synced_at": "2026-06-11T10:01:00Z",  // When synced to internal structure
     "sync_status": "synced" | "pending" | "conflict"
   }
   ```

2. **Sync logic** (new module: `api_football_sync.py`):
   - Fetch data from API-Football → Save to `api_football_raw`
   - Compare raw data with current `teams`/`matches` collections
   - Detect changes (new teams, updated stats, fixture changes)
   - Sync changes to internal structure
   - Flag conflicts (e.g., manual overrides vs. API updates)

**Tasks**:
1. **Cleanup** (Option A):
   - Delete or archive migration scripts (`migrate_to_firestore.py`, `populate_from_api_football.py`)
   - Remove `db_manager` references from comments in `main.py`
   - Delete or fix `test_norway_integration.py`
   - Update documentation to reflect Firestore-only architecture

2. **Add API-Football Raw Storage**:
   - Create `api_football_raw` collection in Firestore
   - Add `save_raw_api_response()` method to `data_aggregator.py`
   - Store team stats, fixtures, predictions as separate documents

3. **Implement Sync Process**:
   - Create `backend/src/api_football_sync.py` module
   - Implement change detection logic (compare raw API data with internal structure)
   - Add `sync_teams()`, `sync_matches()`, `sync_team_stats()` methods
   - Handle conflicts (manual overrides vs. API updates)

4. **Update Existing Flow**:
   - Modify `data_aggregator.py` to save raw responses to `api_football_raw`
   - Add `last_synced_at` timestamp to `teams` and `matches` documents
   - Add `data_source` field: `"api_football"` vs `"manual"`

5. **Testing**:
   - Unit tests for sync logic
   - Integration tests for change detection
   - Test conflict resolution scenarios

**Effort**: 2-3 days  
**Risk**: Low-Medium (additive changes, doesn't break existing flow)  
**Value**: 
- ✅ API-Football as canonical source (audit trail via raw storage)
- ✅ Change detection (know when API data updates)
- ✅ Conflict resolution (manual overrides vs. API)
- ✅ Clean separation of concerns (raw API data vs. internal structure)

**Benefits Over Option A**:
- Traceability: Raw API responses preserved for debugging
- Flexibility: Can replay syncs or rollback changes
- Conflict handling: Detect when manual edits conflict with API updates

**Benefits Over Option B/C**:
- Lower risk: Doesn't require tournament structure sync (can add later)
- Incremental: Can start with team stats, add fixtures later
- No frontend changes: Internal structure remains compatible

---

### Alternative Options (Not Selected)

#### Option B: Optimize API-Football Integration (Medium Risk)
*Superseded by Option A+ which includes caching improvements*

#### Option C: Full API-Football Tournament Structure Sync (High Risk)
*Deferred: Requires World Cup 2026 data availability verification*

---

## Next Steps

### Phase 1: Cleanup (Option A) ✅
1. ✅ Delete or archive migration scripts
2. ✅ Remove legacy `db_manager` references
3. ✅ Update documentation

### Phase 2: API-Football Raw Storage 🔄
1. Create `api_football_raw` Firestore collection
2. Add raw response storage to `data_aggregator.py`
3. Store team stats, fixtures, predictions as documents

### Phase 3: Sync Implementation 🔄
1. Create `backend/src/api_football_sync.py` module
2. Implement change detection logic
3. Add conflict resolution (manual vs. API)
4. Add `last_synced_at` metadata to collections

### Phase 4: Testing & Validation 🔄
1. Unit tests for sync logic
2. Integration tests for change detection
3. Test conflict scenarios
4. Verify frontend compatibility

### Phase 5: Documentation 📝
1. Document sync process architecture
2. Add API-Football raw storage schema
3. Document conflict resolution strategy

---

## Sync Architecture Details

### Change Detection Logic

```python
def detect_team_changes(raw_api_data: dict, current_team: dict) -> dict:
    """
    Compare raw API-Football data with current Firestore team.
    
    Returns:
        {
            "has_changes": bool,
            "changed_fields": list,
            "conflicts": list  // Fields with manual overrides
        }
    """
    changes = {
        "has_changes": False,
        "changed_fields": [],
        "conflicts": []
    }
    
    # Compare name, FIFA code, API ID
    if raw_api_data["name"] != current_team["name"]:
        if current_team.get("data_source") == "manual":
            changes["conflicts"].append("name")
        else:
            changes["changed_fields"].append("name")
            changes["has_changes"] = True
    
    return changes
```

### Conflict Resolution Strategy

**Priority**: Manual overrides take precedence over API updates (with warning)

| Scenario | Action | Example |
|----------|--------|---------|
| API updates team name, no manual override | Auto-sync | "USA" → "United States" |
| API updates team name, manual override exists | Flag conflict, keep manual | Keep "USA", log warning |
| New team appears in API | Auto-add with `data_source: "api_football"` | Add new qualified team |
| Team removed from API | Flag for review, don't delete | Mark as `status: "removed_from_api"` |

### Raw Storage Schema

**Collection**: `api_football_raw`

**Document ID Pattern**: `{type}_{entity_id}_{timestamp}`

Examples:
- `team_stats_16_2026-06-11T10:00:00Z`
- `fixtures_12345_2026-06-11T10:00:00Z`
- `predictions_67890_2026-06-11T10:00:00Z`

**Document Structure**:
```json
{
  "type": "team_stats",
  "entity_id": "16",  // API-Football team ID
  "api_endpoint": "/fixtures?team=16&last=5",
  "request_params": {
    "team": 16,
    "last": 5
  },
  "response_data": {
    "response": [ /* raw API response */ ]
  },
  "fetched_at": "2026-06-11T10:00:00Z",
  "synced_at": "2026-06-11T10:01:00Z",
  "sync_status": "synced",
  "sync_notes": "Updated avg_xg from 1.5 to 1.8"
}
```

---

**End of Research Findings**
