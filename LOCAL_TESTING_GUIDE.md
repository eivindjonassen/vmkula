# Local Testing Setup Guide

**Goal**: Run the complete vmkula-website stack locally to validate end-to-end functionality.

---

## 📋 Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11+ installed (`python3 --version`)
- [ ] Node.js 20+ installed (`node --version`)
- [ ] Firebase project created (project ID: `vmkula`)
- [ ] API keys obtained:
  - [ ] API-Football key (from https://www.api-football.com/)
  - [ ] Gemini API key (from https://aistudio.google.com/apikey)
  - [ ] Firebase service account key (JSON file downloaded)

---

## 🔧 Setup Steps

### Step 1: Verify Environment Variables

Your `.env` file in the root should contain:

```bash
# API Keys
API_FOOTBALL_KEY=your-api-football-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# Firebase/Firestore
FIRESTORE_PROJECT_ID=vmkula
GOOGLE_APPLICATION_CREDENTIALS=/path/to/vmkula-service-account-key.json

# Frontend Firebase Config (these are public - safe to commit)
NEXT_PUBLIC_FIREBASE_API_KEY=your-firebase-api-key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=vmkula.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=vmkula
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=vmkula.firebasestorage.app
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
NEXT_PUBLIC_FIREBASE_APP_ID=your-app-id

# Optional Settings (defaults shown)
CACHE_TTL_HOURS=24
CACHE_DIR=cache
DEBUG=false
```

**Action**: Verify your `.env` file has all required variables set.

---

### Step 2: Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verify database exists
ls -lh worldcup2026.db
# Should show: worldcup2026.db (28KB file)

# Create cache directory
mkdir -p cache
```

---

### Step 3: Run Backend Tests (Optional but Recommended)

```bash
# Still in backend/ directory with venv activated
pytest --cov=src --cov-report=term

# Expected: All tests should pass
# Coverage should be >= 80%
```

**If tests fail**: Check error messages and ensure environment is set up correctly.

---

### Step 4: Start Backend Server

```bash
# Still in backend/ directory with venv activated
uvicorn src.main:app --reload --port 8000

# Expected output:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
# INFO:     Started server process
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
```

**Keep this terminal open** - backend server is now running.

---

### Step 5: Test Backend Health Endpoint

Open a **new terminal** and test the health endpoint:

```bash
curl http://localhost:8000/health

# Expected JSON response:
{
  "status": "healthy",
  "database": "connected",
  "firestore": "connected",
  "cache_size": 0
}
```

**If you get errors**:
- `database: error` → Check `worldcup2026.db` exists in `backend/` directory
- `firestore: error` → Check Firebase credentials and project ID
- Connection refused → Make sure backend server is running (Step 4)

---

### Step 6: Generate Predictions (First Run)

This will trigger the full pipeline: SQLite → FIFA Engine → API-Football → Gemini AI → Firestore

```bash
# In the new terminal (not the one running uvicorn)
curl -X POST http://localhost:8000/api/update-predictions

# Expected response (takes 2-5 minutes):
{
  "status": "success",
  "updated_at": "2025-12-25T21:30:00Z",
  "predictions_generated": 104,
  "errors": []
}
```

**What happens during this call**:
1. ✅ Loads 48 teams and 104 matches from SQLite
2. ✅ Calculates group standings (with Fair Play Points tiebreaker)
3. ✅ Fetches team stats from API-Football (48 teams × 0.5s delay = ~24 seconds)
4. ✅ Generates AI predictions with Gemini (104 matches × 1-2s = ~2-3 minutes)
5. ✅ Publishes to Firestore: `predictions/latest` document
6. ✅ Creates history entries in `matches/{id}/history` sub-collection

**Monitoring Progress**:
- Watch backend terminal for log messages
- Check cache directory: `ls -lh backend/cache/` (should see JSON files)

**If you get errors**:
- `API_FOOTBALL rate limit` → Wait 24 hours or use cached data
- `Gemini API error` → Check API key and quota
- `Firestore permission denied` → Check service account permissions

---

### Step 7: Verify Firestore Data

**Option A: Using Firebase Console** (Recommended)
1. Go to https://console.firebase.google.com/
2. Select project: `vmkula`
3. Navigate to Firestore Database
4. Check for document: `predictions/latest`
5. Should see fields: `groups`, `bracket`, `aiSummary`, `favorites`, `darkHorses`, `updatedAt`

**Option B: Using Firebase MCP Tools** (if configured)
```bash
# List Firestore collections
firebase_firestore_get predictions/latest
```

---

### Step 8: Frontend Setup

Open a **new terminal** (3rd terminal - keep backend running):

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Verify Next.js config
cat next.config.ts
# Should show: no output export, standard Next.js config

# Run frontend dev server
npm run dev

# Expected output:
#   ▲ Next.js 16.1.1
#   - Local:        http://localhost:3000
#   - Ready in 2.5s
```

**Keep this terminal open** - frontend server is now running.

---

### Step 9: Test Frontend in Browser

1. Open browser: http://localhost:3000
2. **Expected behavior**:
   - Loading spinner appears briefly
   - Tabs visible: Groups | Matches | Bracket
   - Data loads from Firestore
   - Last updated timestamp shows

3. **Test each tab**:
   - **Groups**: Should show 12 groups (A-L) with team standings
   - **Matches**: Should show 104 matches with predictions
   - **Bracket**: Should show knockout bracket tree

4. **Test features**:
   - Group filtering (on Groups page)
   - Stage filtering (on Matches page)
   - Search by team name (on Matches page)
   - Zoom controls (on Bracket page)
   - "Refresh Predictions" button (should trigger backend update)

---

### Step 10: Frontend Tests (Optional)

```bash
# In frontend/ directory
npm test

# Expected: All tests should pass
# Some tests may have known issues (e.g., GroupCard test design flaw)
```

---

## 🐛 Troubleshooting

### Backend Issues

**Error: "Missing required environment variables"**
- Check `.env` file exists in project root
- Verify all required variables are set (see Step 1)
- Restart backend server after changing `.env`

**Error: "Database not found"**
- Verify `worldcup2026.db` exists in `backend/` directory
- Check file size: should be ~28KB
- If missing, restore from git history

**Error: "Firestore permission denied"**
- Check service account key path in `GOOGLE_APPLICATION_CREDENTIALS`
- Verify service account has "Cloud Datastore User" role
- Re-download service account key from Firebase Console

**Error: "API-Football rate limit exceeded"**
- Free tier: 100 requests/day
- Wait 24 hours OR use existing cache
- Cache files in `backend/cache/` are valid for 24 hours

**Error: "Gemini API quota exceeded"**
- Check quota: https://aistudio.google.com/
- Free tier: 15 requests/minute, 1500 requests/day
- Wait for quota reset OR use rule-based fallback (automatic)

### Frontend Issues

**Error: "Firebase: No Firebase App '[DEFAULT]' has been created"**
- Check frontend `.env` variables are prefixed with `NEXT_PUBLIC_`
- Verify Firebase config is correct (API key, project ID, etc.)
- Restart frontend dev server after changing `.env`

**Blank page / No data loading**
- Check browser console (F12) for errors
- Verify Firestore data exists: `predictions/latest` document
- Check network tab: should see Firestore requests
- Verify CORS settings in Firebase (should allow localhost)

**Error: "Document 'predictions/latest' not found"**
- Backend hasn't published data yet
- Run Step 6 (Generate Predictions) first
- Check backend terminal for errors during publish

---

## ✅ Success Criteria

You'll know everything is working when:

1. ✅ Backend health endpoint returns `status: healthy`
2. ✅ `/api/update-predictions` completes successfully (104 predictions generated)
3. ✅ Firestore document `predictions/latest` exists with data
4. ✅ Frontend loads at http://localhost:3000
5. ✅ All 3 tabs display data (Groups, Matches, Bracket)
6. ✅ Predictions show team names, scores, win probabilities, reasoning
7. ✅ Group standings show correct sorting (points, GD, goals, fair play)
8. ✅ Bracket shows knockout matchups with TBD placeholders for future rounds

---

## 📊 Expected Performance

- **Backend startup**: < 5 seconds
- **First prediction generation**: 2-5 minutes (API calls + AI predictions)
- **Subsequent predictions (cached)**: < 30 seconds
- **Frontend page load**: < 2 seconds
- **Firestore data fetch**: < 500ms

---

## 🔄 Next Steps After Local Testing

Once local testing is successful:

1. **Document Issues**: Note any errors encountered for Phase 4 integration tests
2. **Phase 4**: Run `/implement vmkula-website phase 4` - Integration & Polish
3. **Deploy**: Set up Cloud Run (backend) + Firebase Hosting (frontend)
4. **Cloud Scheduler**: Configure daily prediction updates

---

## 📝 Notes

- **First run**: Takes 2-5 minutes due to API calls (API-Football + Gemini)
- **Cached runs**: Much faster (~30 seconds) if cache is valid (<24 hours)
- **Cost optimization**: Cache is aggressive to stay within free tier limits
- **Data freshness**: Predictions refresh when manually triggered or via scheduled job

---

**Need help?** Check error messages in:
- Backend terminal (uvicorn logs)
- Frontend terminal (Next.js logs)
- Browser console (F12 → Console tab)
- Firestore console (Firebase UI)
