# Migration Testing Guide

This guide helps you test the SQLite → Firestore migration to verify everything works correctly before final cleanup.

## Prerequisites

1. **Firestore data migrated**
   ```bash
   cd backend
   python migrate_to_firestore.py
   ```
   
   Expected output: "Migration completed! 48 teams, 104 matches, 16 cities migrated to Firestore"

2. **Environment variables configured**
   ```bash
   # Check .env file has:
   FIRESTORE_PROJECT_ID=your-project-id
   API_FOOTBALL_KEY=your-api-key
   GEMINI_API_KEY=your-gemini-key
   ```

3. **Dependencies installed**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

## Option 1: Automated Testing (Recommended)

### Step 1: Start the Backend Server

```bash
cd backend
python src/main.py
```

Expected output:
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080 (Press CTRL+C to quit)
```

### Step 2: Run Test Suite (in new terminal)

```bash
cd backend
python test_migration.py
```

Expected output:
```
================================================================================
                   FIRESTORE MIGRATION TEST SUITE
================================================================================

ℹ️  Testing backend at: http://localhost:8080
ℹ️  Timestamp: 2025-12-26T15:00:00Z

================================================================================
                        TEST 1: Health Endpoint
================================================================================

ℹ️  Response: {
  "status": "healthy",
  "firestore": "ok",
  "teams_count": 48,
  "matches_count": 104
}
✅ Health check passed: 48 teams in Firestore

================================================================================
                   TEST 2: Update Tournament (Load from Firestore)
================================================================================

ℹ️  Calling POST /api/update-tournament...
ℹ️  Response: {
  "status": "success",
  "updated_at": "2025-12-26T15:00:00Z"
}
✅ Tournament update successful (loaded from Firestore)

================================================================================
              TEST 3: Update Predictions (1st Run - Cold Cache)
================================================================================

ℹ️  Calling POST /api/update-predictions (first run)...
⚠️  This may take 2-3 minutes (fetching stats + generating predictions)
ℹ️  Duration: 120.5 seconds

📊 First Run Metrics:
  - Team Stats Cache Hits: 0
  - Team Stats Cache Misses: 48
  - Predictions Cached: 0
  - Predictions Regenerated: 72

✅ ✓ Cold cache working: 48 stats fetched from API
✅ ✓ Predictions generated: 72 new predictions

================================================================================
              TEST 4: Update Predictions (2nd Run - Hot Cache)
================================================================================

ℹ️  Calling POST /api/update-predictions (second run)...
ℹ️  Expected: ALL cache hits, ZERO API calls
ℹ️  Duration: 2.3 seconds

📊 Second Run Metrics:
  - Team Stats Cache Hits: 48
  - Team Stats Cache Misses: 0
  - Predictions Cached: 72
  - Predictions Regenerated: 0

✅ ✓ 100% cache hit rate: 48 stats from Firestore cache
✅ ✓ 100% prediction cache: 72 cached (0 API calls!)

🎉 COST SAVINGS: 100% cache hit = $0 API costs (vs ~$0.01 without caching)!

================================================================================
                          TEST SUMMARY
================================================================================

✅ Health Endpoint: PASSED
✅ Update Tournament: PASSED
✅ Predictions (1st run): PASSED
✅ Predictions (2nd run): PASSED
✅ Data Integrity: PASSED

Results: 5/5 tests passed

🎉 ALL TESTS PASSED! Migration successful!

Next steps:
  1. Manually verify frontend displays correctly
  2. Backup SQLite database: cp backend/worldcup2026.db backend/worldcup2026.db.backup
  3. Proceed to Phase 4 cleanup (optional)
```

## Option 2: Manual Testing

If you prefer to test manually:

### Test 1: Health Check

```bash
curl http://localhost:8080/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "firestore": "ok",
  "teams_count": 48,
  "matches_count": 104
}
```

**Success criteria:**
- ✅ Status is "healthy"
- ✅ Firestore is "ok"
- ✅ teams_count > 0
- ✅ matches_count > 0

### Test 2: Update Tournament

```bash
curl -X POST http://localhost:8080/api/update-tournament
```

**Expected response:**
```json
{
  "status": "success",
  "updated_at": "2025-12-26T15:00:00Z",
  "groups_count": 12,
  "matches_count": 104
}
```

**Success criteria:**
- ✅ Status is "success"
- ✅ Has updated_at timestamp
- ✅ No errors in backend logs

### Test 3: First Predictions Run (Cold Cache)

```bash
curl -X POST http://localhost:8080/api/update-predictions
```

**Expected behavior:**
- ⏱️ Takes 2-3 minutes (fetching stats from API-Football)
- 📊 Response shows cache misses and regenerated predictions

**Expected response:**
```json
{
  "status": "success",
  "firestore_cache_hits": 0,
  "firestore_cache_misses": 48,
  "predictions_cached": 0,
  "predictions_regenerated": 72,
  "updated_at": "2025-12-26T15:00:00Z"
}
```

**Success criteria:**
- ✅ firestore_cache_misses > 0 (first run fetches from API)
- ✅ predictions_regenerated > 0 (first run generates predictions)
- ✅ No errors in backend logs

### Test 4: Second Predictions Run (Hot Cache)

```bash
curl -X POST http://localhost:8080/api/update-predictions
```

**Expected behavior:**
- ⚡ Fast (< 5 seconds) - using cached data
- 📊 Response shows cache hits and cached predictions

**Expected response:**
```json
{
  "status": "success",
  "firestore_cache_hits": 48,
  "firestore_cache_misses": 0,
  "predictions_cached": 72,
  "predictions_regenerated": 0,
  "updated_at": "2025-12-26T15:00:00Z"
}
```

**Success criteria:**
- ✅ firestore_cache_hits = 48 (ALL teams cached)
- ✅ firestore_cache_misses = 0 (NO API calls)
- ✅ predictions_cached > 0 (predictions reused)
- ✅ predictions_regenerated = 0 (NO Gemini calls)
- ✅ **COST SAVINGS: $0** (vs ~$0.01 without caching)

### Test 5: Frontend Verification

1. **Deploy/run frontend** (if not already running)
   ```bash
   cd frontend
   npm run dev
   ```

2. **Open in browser**: http://localhost:3000

3. **Verify:**
   - ✅ Matches display correctly
   - ✅ Predictions show up
   - ✅ Team names correct
   - ✅ Badges (Live/Test) work
   - ✅ No console errors

## Backend Logs to Check

When running tests, check backend logs for:

### ✅ Good Signs

```
✅ Cache HIT for team 36
✅ Stats unchanged for match 1, using cached prediction
✅ Firestore cache hits: 48/48 (100%)
✅ Predictions cached: 72/72 (100%)
```

### ❌ Warning Signs

```
❌ Cache EXPIRED for team 36
❌ Stats changed for match 1, regenerating prediction
⚠️  Firestore operation failed: ...
⚠️  Failed to fetch team stats: ...
```

## Troubleshooting

### Problem: Backend won't start

**Solution:**
```bash
# Check environment variables
cat backend/.env

# Check dependencies
cd backend
pip install -r requirements.txt

# Check logs
python src/main.py
```

### Problem: "Firestore not OK" in health check

**Solution:**
```bash
# Verify Firestore project ID
echo $FIRESTORE_PROJECT_ID

# Re-run migration
cd backend
python migrate_to_firestore.py

# Check Firestore console
# https://console.firebase.google.com/project/YOUR_PROJECT/firestore
```

### Problem: Cache always misses (0 hits)

**Solution:**
```bash
# Check Firestore has team stats
# Run first predictions to populate cache
curl -X POST http://localhost:8080/api/update-predictions

# Wait for completion, then run again
curl -X POST http://localhost:8080/api/update-predictions
# ^ Should show cache hits now
```

### Problem: Predictions always regenerate

**Possible causes:**
- Team stats expired (TTL = 24 hours)
- Team stats hash changed (stats updated from API)
- First run (no cached predictions yet)

**Check:**
```bash
# Run twice in succession
curl -X POST http://localhost:8080/api/update-predictions
# Wait 5 seconds
curl -X POST http://localhost:8080/api/update-predictions
# ^ Second run should show 100% cached
```

## Success Criteria Summary

Before proceeding to Phase 4 cleanup, verify:

- [ ] Health endpoint shows "firestore": "ok"
- [ ] Health endpoint shows teams_count > 0
- [ ] Tournament update loads from Firestore successfully
- [ ] First predictions run fetches stats (cache misses)
- [ ] Second predictions run uses cache (100% hits)
- [ ] Cache savings confirmed (0 API calls on 2nd run)
- [ ] Frontend displays matches correctly
- [ ] No errors in backend logs
- [ ] No errors in frontend console

## Next Steps

### If All Tests Pass ✅

1. **Backup SQLite database**
   ```bash
   cp backend/worldcup2026.db backend/worldcup2026.db.backup
   ```

2. **Update MIGRATION_PROGRESS.md** with test results

3. **Proceed to Phase 4** (optional cleanup):
   - Remove SQLite file (keep backup)
   - Remove `db_manager.py` (keep for reference)
   - Update tests
   - Update documentation

### If Tests Fail ❌

1. **Review error messages** in test output
2. **Check backend logs** for stack traces
3. **Verify Firestore data** in Firebase Console
4. **Re-run migration** if data is missing
5. **Ask for help** with specific error messages

## Cost Savings Verification

**Before migration:**
- Every `/api/update-predictions` call = ~144 API-Football calls + 72 Gemini calls = $0.01

**After migration:**
- First run (cold cache) = ~144 API-Football calls + 72 Gemini calls = $0.01
- Second run (hot cache) = **0 API calls + 0 Gemini calls = $0**
- Daily runs (refresh changed teams) = ~30 API calls + ~10 Gemini calls = $0.001

**Savings: 90-100%** 🎉

## Contact

If you encounter issues:
1. Check backend logs
2. Check Firestore console
3. Re-run migration script
4. Review MIGRATION_PLAN.md for architecture details
