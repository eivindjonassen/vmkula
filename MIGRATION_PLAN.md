# Migration Plan: SQLite → Firestore + API-Football

## Overview

**Goal**: Remove `worldcup2026.db` and use Firestore + API-Football as the single source of truth.

**Benefits**:
- ✅ Single source of truth (no data duplication)
- ✅ Real-time updates across frontend/backend
- ✅ Automatic data freshness from API-Football
- ✅ Smart caching to minimize API calls
- ✅ Simpler architecture (no SQLite maintenance)

## Current Architecture (Before)

```
┌─────────────────┐
│ SQLite Database │ ← Static data (teams, matches, venues)
│ worldcup2026.db │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ API-Football    │ ← Team stats only
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Gemini AI       │ ← Predictions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Firestore       │ ← Predictions + snapshot
└─────────────────┘
```

**Problems**:
- ❌ Teams stored in both SQLite and Firestore
- ❌ Match data duplicated
- ❌ Static data gets stale
- ❌ Must manually update SQLite when fixtures change

## New Architecture (After)

```
┌─────────────────┐
│ API-Football    │ ← Teams, fixtures, stats, predictions
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Firestore       │ ← Everything (teams, matches, predictions, cache)
│  Collections:   │
│  - teams        │
│  - matches      │
│  - predictions  │
│  - api_cache    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Gemini AI       │ ← Only when needed
└─────────────────┘
```

**Benefits**:
- ✅ Single source of truth (Firestore)
- ✅ API-Football provides fresh data
- ✅ Smart caching prevents redundant API calls
- ✅ No SQLite to maintain

## Firestore Schema Design

### Collection: `teams`

```javascript
teams/{team_id}
{
  id: number,
  name: string,
  fifa_code: string,
  api_football_id: number,  // Link to API-Football team
  group: string,
  
  // Stats (cached from API-Football)
  stats: {
    form_string: string,      // "W-W-D-W-L"
    clean_sheets: number,
    avg_xg: number | null,
    confidence: string,
    has_real_data: boolean,
    
    // Cache metadata
    fetched_at: timestamp,
    expires_at: timestamp,    // 24 hours from fetched_at
  }
}
```

**Example**:
```javascript
teams/36 (Norway)
{
  id: 36,
  name: "Norway",
  fifa_code: "NOR",
  api_football_id: 1090,
  group: "I",
  stats: {
    form_string: "W-W-D-W-W",
    clean_sheets: 1,
    avg_xg: null,
    confidence: "low",
    has_real_data: true,
    fetched_at: "2025-12-26T12:00:00Z",
    expires_at: "2025-12-27T12:00:00Z"
  }
}
```

### Collection: `matches`

```javascript
matches/{match_id}
{
  id: number,
  match_number: number,
  
  home_team_id: number,
  away_team_id: number,
  home_team_name: string,
  away_team_name: string,
  
  // Match details (from API-Football when linked)
  api_football_fixture_id: number | null,  // Link to API-Football fixture
  kickoff: timestamp,
  venue: string,
  city: string,
  stage_id: number,
  label: string,
  
  // Prediction (cached from Gemini)
  prediction: {
    winner: string,
    win_probability: number,
    predicted_home_score: number,
    predicted_away_score: number,
    reasoning: string,
    confidence: string,
    
    // API-Football prediction (when available)
    api_football_prediction: {
      home_percent: string,
      draw_percent: string,
      away_percent: string,
      advice: string
    } | null,
    
    // Cache metadata
    generated_at: timestamp,
    expires_at: timestamp,    // Regenerate when team stats change
    team_stats_hash: string,  // Hash of team stats used
  },
  
  has_real_data: boolean
}
```

### Collection: `api_cache`

For caching API-Football responses:

```javascript
api_cache/{cache_key}
{
  key: string,              // "prediction_12345" or "stats_1090"
  data: object,             // Raw API response
  fetched_at: timestamp,
  expires_at: timestamp,    // 24 hours
}
```

### Collection: `tournament_snapshot` (Legacy)

Keep for backward compatibility:

```javascript
predictions/latest
{
  groups: {...},
  matches: [...],
  bracket: [...],
  predictions: [...],
  updated_at: timestamp,
  ai_summary: string
}
```

## Smart Caching Strategy

### 1. Team Stats Caching

**Location**: Firestore `teams/{team_id}.stats`

**Cache Key**: Team ID  
**TTL**: 24 hours  
**Invalidation**: Expires at midnight or on manual refresh

**Logic**:
```python
def fetch_team_stats(team_id):
    # 1. Check Firestore cache
    team_doc = db.collection('teams').document(str(team_id)).get()
    
    if team_doc.exists:
        stats = team_doc.to_dict().get('stats')
        
        # Check if cache is fresh
        if stats and stats['expires_at'] > datetime.now():
            logger.info(f"✅ Cache HIT for team {team_id}")
            return stats
    
    # 2. Cache MISS - Fetch from API-Football
    logger.info(f"❌ Cache MISS for team {team_id}")
    api_stats = fetch_from_api_football(team_id)
    
    # 3. Update Firestore cache
    db.collection('teams').document(str(team_id)).set({
        'stats': {
            **api_stats,
            'fetched_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24)
        }
    }, merge=True)
    
    return api_stats
```

### 2. Prediction Caching

**Location**: Firestore `matches/{match_id}.prediction`

**Cache Key**: Match ID + Team Stats Hash  
**TTL**: Until team stats change  
**Invalidation**: When team stats are refreshed

**Logic**:
```python
def generate_prediction(match_id, home_stats, away_stats):
    # 1. Calculate hash of team stats
    stats_hash = hash_stats(home_stats, away_stats)
    
    # 2. Check if prediction exists and is still valid
    match_doc = db.collection('matches').document(str(match_id)).get()
    
    if match_doc.exists:
        prediction = match_doc.to_dict().get('prediction')
        
        if prediction and prediction['team_stats_hash'] == stats_hash:
            logger.info(f"✅ Prediction CACHED for match {match_id}")
            return prediction
    
    # 3. Cache MISS - Generate new prediction with Gemini
    logger.info(f"❌ Prediction needs regeneration for match {match_id}")
    new_prediction = call_gemini(home_stats, away_stats)
    
    # 4. Update Firestore
    db.collection('matches').document(str(match_id)).set({
        'prediction': {
            **new_prediction,
            'generated_at': datetime.now(),
            'team_stats_hash': stats_hash
        }
    }, merge=True)
    
    return new_prediction

def hash_stats(home_stats, away_stats):
    """Create hash of team stats to detect changes."""
    import hashlib
    stats_str = f"{home_stats}{away_stats}"
    return hashlib.md5(stats_str.encode()).hexdigest()
```

### 3. API-Football Response Caching

**Location**: Firestore `api_cache/{cache_key}` OR local file cache

**Cache Key**: Endpoint + Parameters  
**TTL**: 24 hours  
**Invalidation**: Time-based

**Decision**: Keep local file cache for API-Football responses (already implemented) to avoid Firestore read costs.

## Migration Steps

### Phase 1: Preparation (No Breaking Changes)

**Tasks**:
1. ✅ Analyze SQLite schema
2. ✅ Design Firestore schema
3. ✅ Document migration plan
4. ⏳ Create Firestore collections (teams, matches)
5. ⏳ Implement helper functions for Firestore operations

**Duration**: 1-2 hours

### Phase 2: Dual-Write (Transition Period)

**Tasks**:
1. Update `main.py` to write to BOTH SQLite and Firestore
2. Populate Firestore `teams` collection from SQLite
3. Populate Firestore `matches` collection from SQLite
4. Add cache metadata (fetched_at, expires_at)
5. Verify data consistency

**Duration**: 2-3 hours

### Phase 3: Switch Reads to Firestore

**Tasks**:
1. Update `main.py` to READ from Firestore (still write to both)
2. Test all endpoints
3. Verify frontend still works
4. Monitor for issues

**Duration**: 1-2 hours

### Phase 4: Remove SQLite (Clean Up)

**Tasks**:
1. Remove SQLite writes from code
2. Remove `db_manager.py`
3. Remove `worldcup2026.db` file
4. Update tests
5. Update documentation

**Duration**: 1 hour

## API Call Optimization

### Current State (Wasteful)

Every `/api/update-predictions` call:
- Fetches stats for ALL teams (even if cached)
- Regenerates ALL predictions (even if stats unchanged)
- Cost: ~72 Gemini calls = $0.01

### New State (Optimized)

```python
def update_predictions():
    teams = get_all_teams_from_firestore()
    
    # Step 1: Only fetch stats for teams with expired cache
    teams_to_refresh = []
    for team in teams:
        if team.stats.expires_at < now():
            teams_to_refresh.append(team)
    
    logger.info(f"Refreshing stats for {len(teams_to_refresh)}/{len(teams)} teams")
    
    # Step 2: Only regenerate predictions where team stats changed
    predictions_to_generate = []
    for match in matches:
        current_hash = hash_stats(home_stats, away_stats)
        cached_hash = match.prediction.team_stats_hash
        
        if current_hash != cached_hash:
            predictions_to_generate.append(match)
    
    logger.info(f"Regenerating {len(predictions_to_generate)}/{len(matches)} predictions")
    
    # Result: Massive savings!
    # - First run: 72 predictions
    # - Subsequent runs (same day): 0 predictions (if stats unchanged)
```

### Expected Savings

| Scenario | API-Football Calls | Gemini Calls | Cost |
|----------|-------------------|--------------|------|
| **First run (cold)** | ~144 (48 teams × 3) | 72 | $0.01 |
| **Second run (same day)** | 0 (cached) | 0 (stats unchanged) | $0 |
| **Next day (stats refresh)** | ~144 (refresh stats) | ~5-10 (only changed) | $0.001 |

## Code Changes Required

### 1. New File: `backend/src/firestore_manager.py`

```python
"""Firestore data management for teams and matches."""

class FirestoreManager:
    def __init__(self):
        self.db = firestore.Client()
    
    # Teams
    def get_team(self, team_id: int) -> Dict:
        """Get team with cached stats."""
        pass
    
    def get_all_teams(self) -> List[Dict]:
        """Get all teams."""
        pass
    
    def update_team_stats(self, team_id: int, stats: Dict):
        """Update team stats with cache metadata."""
        pass
    
    # Matches
    def get_match(self, match_id: int) -> Dict:
        """Get match with prediction."""
        pass
    
    def get_all_matches(self) -> List[Dict]:
        """Get all matches."""
        pass
    
    def update_match_prediction(self, match_id: int, prediction: Dict):
        """Update match prediction with cache metadata."""
        pass
    
    # Cache helpers
    def is_cache_fresh(self, expires_at: datetime) -> bool:
        """Check if cache is still valid."""
        return expires_at > datetime.now()
    
    def calculate_stats_hash(self, *stats: Dict) -> str:
        """Calculate hash of team stats."""
        import hashlib
        stats_str = str(sorted(str(s) for s in stats))
        return hashlib.md5(stats_str.encode()).hexdigest()
```

### 2. Update: `backend/src/main.py`

**Before**:
```python
# Get teams from SQLite
teams = db_manager.get_all_teams()
```

**After**:
```python
# Get teams from Firestore
teams = firestore_manager.get_all_teams()
```

### 3. One-Time Migration Script: `backend/migrate_to_firestore.py`

```python
"""Migrate data from SQLite to Firestore."""

def migrate():
    # 1. Migrate teams
    teams = sqlite_db.get_all_teams()
    for team in teams:
        firestore.collection('teams').document(str(team.id)).set({
            'id': team.id,
            'name': team.name,
            'fifa_code': team.fifa_code,
            'api_football_id': team.api_football_id,
            'group': team.group,
            'stats': None  # Will be populated on first API call
        })
    
    # 2. Migrate matches
    matches = sqlite_db.get_all_matches()
    for match in matches:
        firestore.collection('matches').document(str(match.id)).set({
            'id': match.id,
            'match_number': match.match_number,
            'home_team_id': match.home_team_id,
            'away_team_id': match.away_team_id,
            # ... other fields
            'prediction': None  # Will be generated
        })
```

## Testing Plan

### Unit Tests

```bash
# Test Firestore operations
pytest backend/tests/test_firestore_manager.py -v

# Test cache logic
pytest backend/tests/test_caching.py -v
```

### Integration Tests

```bash
# Test full prediction pipeline
pytest backend/tests/test_integration.py -v
```

### Manual Testing

1. Run migration script
2. Call `/api/update-predictions` (should fetch all stats)
3. Check Firestore for populated data
4. Call `/api/update-predictions` again (should use cache, 0 API calls)
5. Verify frontend displays correctly

## Rollback Plan

If migration fails:

1. Keep SQLite file as backup
2. Switch reads back to SQLite
3. Debug Firestore issues
4. Retry migration

**Backup command**:
```bash
cp backend/worldcup2026.db backend/worldcup2026.db.backup
```

## Timeline

| Phase | Duration | Cumulative |
|-------|----------|------------|
| Phase 1: Preparation | 2 hours | 2 hours |
| Phase 2: Dual-Write | 3 hours | 5 hours |
| Phase 3: Switch Reads | 2 hours | 7 hours |
| Phase 4: Cleanup | 1 hour | 8 hours |

**Total**: ~8 hours

## Success Criteria

- ✅ All teams in Firestore with correct data
- ✅ All matches in Firestore with correct data
- ✅ Predictions cached and regenerated only when needed
- ✅ API calls reduced by 90%+ on subsequent runs
- ✅ Frontend displays correctly
- ✅ No SQLite dependencies remaining
- ✅ Tests passing

## Next Steps

Would you like me to:
1. **Start Phase 1** - Create Firestore collections and helper functions?
2. **Create migration script** - One-time data migration?
3. **Something else** - Different approach?
