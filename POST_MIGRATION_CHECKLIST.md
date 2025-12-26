# Post-Migration Checklist

**Migration Completed**: 2025-12-26  
**Status**: ✅ Backend fully migrated and tested

---

## Immediate Actions (Before Production Deploy)

### 1. Manual Frontend Verification ⏳

**Why**: Ensure frontend still works with Firestore backend

**Steps**:
```bash
# If frontend not running, start it:
cd frontend
npm run dev

# Open browser: http://localhost:3000
```

**Verify**:
- [ ] Home page loads without errors
- [ ] Matches display correctly
- [ ] Predictions show up
- [ ] Team names are correct
- [ ] Group standings work
- [ ] Bracket view works
- [ ] No console errors in browser DevTools

**Expected**: Everything should work as before (backend API unchanged)

---

### 2. Staging Deployment (Recommended)

**Why**: Test in production-like environment before going live

**Steps**:
```bash
# Deploy backend to staging
cd backend
# Use your deployment method (Cloud Run, App Engine, etc.)

# Deploy frontend to staging
cd frontend
# Use your deployment method
```

**Verify**:
- [ ] Staging backend health check passes
- [ ] Staging frontend loads correctly
- [ ] Test `/api/update-predictions` on staging
- [ ] Check Firestore data in Firebase Console

---

### 3. Monitor for 24-48 Hours

**Why**: Catch any edge cases or unexpected behavior

**What to Monitor**:
- [ ] Backend logs (no errors)
- [ ] Firestore read/write counts
- [ ] Cache hit rates (should be high)
- [ ] API-Football quota usage (should be low)
- [ ] Gemini API usage (should be low)
- [ ] Response times (should be fast)

**Tools**:
- Firebase Console → Firestore → Usage
- Backend logs → Cloud Logging
- API-Football dashboard
- Google AI Studio → Gemini usage

---

## Production Deployment

### Prerequisites

✅ All these should be checked:
- [x] All backend tests passing
- [x] Smart caching validated
- [x] Cost savings confirmed
- [x] Backup created
- [ ] Frontend manually tested
- [ ] Staging environment tested (if available)
- [ ] 24-48h monitoring completed (if staging used)

### Deployment Steps

1. **Deploy Backend**
   ```bash
   cd backend
   # Your deployment command here
   # Example: gcloud run deploy vmkula-backend --source .
   ```

2. **Deploy Frontend**
   ```bash
   cd frontend
   # Your deployment command here
   # Example: npm run build && firebase deploy --only hosting
   ```

3. **Verify Production**
   - [ ] Health check: `curl https://your-backend-url/health`
   - [ ] Open frontend URL and verify
   - [ ] Test predictions update manually (if safe)

---

## Post-Production Monitoring (First Week)

### Day 1-3: Critical Monitoring

**Check Daily**:
- [ ] Backend health check passes
- [ ] No errors in logs
- [ ] Cache hit rate > 90%
- [ ] API costs are low
- [ ] Frontend works correctly
- [ ] Users can access predictions

**Red Flags** (if any occur, investigate immediately):
- ❌ Cache hit rate < 50%
- ❌ Firestore errors in logs
- ❌ High API-Football usage
- ❌ Frontend errors
- ❌ Slow response times

### Day 4-7: Routine Monitoring

**Check Every 2-3 Days**:
- [ ] Firestore usage trends
- [ ] Cost trends (should be lower)
- [ ] Performance metrics
- [ ] User feedback (if any)

---

## Optional Enhancements (Next 2-4 Weeks)

### Priority 1: Add More API-Football Team Mappings

**Current Status**: Only 3 teams have real API-Football data
- Norway (1090)
- France (2)
- Senegal (13)

**Goal**: Map all 48 teams to API-Football IDs

**How**:
1. Research API-Football team IDs
2. Update Firestore `teams` collection
3. Test predictions improve with real data

**Benefit**: Better prediction quality for all teams

---

### Priority 2: Create Unit Tests

**What**:
```bash
# Create these test files:
backend/tests/test_firestore_manager.py
backend/tests/test_caching.py
```

**Why**: Ensure caching logic stays correct

**Tests to Add**:
- [ ] FirestoreManager CRUD operations
- [ ] Cache expiration logic
- [ ] Hash-based change detection
- [ ] Timezone handling

---

### Priority 3: Add Monitoring/Alerting

**What**: Set up alerts for:
- Cache hit rate drops below 80%
- Firestore errors
- High API usage
- Slow response times

**How**:
- Use Firebase/GCP monitoring
- Set up email/Slack alerts
- Create dashboard for key metrics

---

## Cleanup (After 30 Days of Stability)

**If everything is working perfectly for 30+ days:**

### Optional: Remove SQLite Files

```bash
# Only do this if you're 100% confident!
cd backend

# Remove original database
rm worldcup2026.db

# Remove db_manager.py
rm src/db_manager.py

# Keep the backup for another 30 days
# rm worldcup2026.db.backup  # Maybe later
```

**Before removing**:
- [ ] 30+ days of successful operation
- [ ] No issues reported
- [ ] Backup still exists
- [ ] Git history preserved

---

## Performance Baseline (For Comparison)

### Expected Metrics (After Migration)

**First Run of the Day**:
- Team stats cache hits: 0-20 (depends on cache expiry)
- Predictions regenerated: 0-72 (depends on stats changes)
- Execution time: 20-40 seconds
- Cost: $0.001 - $0.01

**Subsequent Runs (Same Day)**:
- Team stats cache hits: 42-48 (100%)
- Predictions cached: 72 (100%)
- Execution time: 8-12 seconds
- Cost: **$0**

**If metrics differ significantly, investigate why**

---

## Troubleshooting Guide

### Issue: Cache Hit Rate Low (<50%)

**Possible Causes**:
- Cache expiry too short
- Team stats changing too frequently
- Timezone issues

**Solution**:
1. Check Firestore data expiration times
2. Increase TTL if needed (currently 24h)
3. Check logs for cache-related errors

---

### Issue: High API-Football Usage

**Possible Causes**:
- Cache not working
- Too many prediction updates
- Stats expiring too quickly

**Solution**:
1. Verify cache hit rate in logs
2. Check cache expiration logic
3. Consider increasing TTL

---

### Issue: Predictions Not Updating

**Possible Causes**:
- Cache too aggressive (stats changed but hash same)
- Firestore write errors
- Permission issues

**Solution**:
1. Check backend logs for errors
2. Verify Firestore write permissions
3. Check hash calculation logic

---

### Issue: Frontend Errors

**Possible Causes**:
- API endpoint changed
- Data format changed
- CORS issues

**Solution**:
1. Check browser console for errors
2. Verify API responses
3. Check CORS configuration

---

## Rollback Procedure (If Needed)

**If critical issues arise and you need to rollback:**

### Step 1: Stop Current Deployment
```bash
# Stop accepting traffic to new backend
# (method depends on your hosting)
```

### Step 2: Revert Code
```bash
cd backend
git log --oneline  # Find commit before migration
git checkout <commit-hash> src/main.py
```

### Step 3: Redeploy Old Version
```bash
# Deploy with SQLite backend
# Your deployment command here
```

### Step 4: Verify Rollback
- [ ] Backend using SQLite again
- [ ] Health check passes
- [ ] Predictions work
- [ ] Frontend works

### Step 5: Investigate Issue
- Review logs
- Identify root cause
- Fix and retry migration

---

## Success Indicators

**After 1 Week**:
- ✅ Zero production incidents
- ✅ Cache hit rate > 90%
- ✅ API costs reduced 90%+
- ✅ Response times improved
- ✅ No user complaints

**After 1 Month**:
- ✅ Stable operation
- ✅ Cost savings confirmed
- ✅ Performance consistently good
- ✅ Ready for enhancements

---

## Documentation References

**Migration Documentation**:
- `MIGRATION_PLAN.md` - Architecture and design
- `MIGRATION_PROGRESS.md` - Step-by-step progress
- `MIGRATION_COMPLETE.md` - Completion status
- `MIGRATION_SUMMARY.md` - Executive summary
- `TESTING_GUIDE.md` - How to test

**Code**:
- `backend/src/firestore_manager.py` - Firestore operations
- `backend/src/main.py` - Updated endpoints
- `backend/test_migration.py` - Test suite

**Backup**:
- `backend/worldcup2026.db` - Original database
- `backend/worldcup2026.db.backup` - Backup copy

---

## Questions to Track

As you use the system, track answers to these:

1. **What is the actual cache hit rate over time?**
   - Day 1: ___
   - Week 1: ___
   - Month 1: ___

2. **What are actual API costs?**
   - Week 1: $___
   - Month 1: $___
   - Savings vs before: ___%

3. **Any unexpected issues?**
   - Issue: ___
   - Solution: ___

4. **What improvements would help?**
   - Idea: ___
   - Priority: ___

---

## Contact & Support

**If you need help**:
1. Review migration documentation
2. Check backend logs
3. Run test suite: `python backend/test_migration.py`
4. Check Firestore Console for data issues
5. Review this checklist for common issues

---

**Last Updated**: 2025-12-26  
**Migration Status**: ✅ Complete  
**Production Status**: ⏳ Awaiting deployment

**Good luck with your production deployment! 🚀**
