# World Cup 2026 Predictions Backend

AI-powered prediction engine for the FIFA World Cup 2026, built with Python, FastAPI, and Google Gemini AI.

## 🏗️ Architecture Overview

```
┌─────────────────┐
│   FastAPI API   │
│  (Cloud Run)    │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────────┐
│SQLite │ │Firestore  │
│ (DB)  │ │ (Cache)   │
└───┬───┘ └───────────┘
    │
┌───▼───────────────────────────┐
│ Prediction Pipeline:          │
│ 1. FIFA Engine (Standings)    │
│ 2. Data Aggregator (Stats)    │
│ 3. AI Agent (Gemini)          │
│ 4. Firestore Publisher        │
└───────────────────────────────┘
```

### Core Philosophy

**"Logic in Python, Magic in AI"**

- **Python**: Calculates group standings, third-place qualifiers, knockout brackets using FIFA rules
- **AI**: Generates match predictions based on team statistics and form

### Key Components

- **`db_manager.py`**: SQLite interface for tournament structure (teams, matches, venues)
- **`fifa_engine.py`**: FIFA World Cup rules engine (standings, tiebreakers, bracket resolution)
- **`data_aggregator.py`**: Team statistics from API-Football (xG, form, clean sheets)
- **`ai_agent.py`**: Gemini AI prediction service with retry/fallback logic
- **`firestore_publisher.py`**: Firestore integration for predictions storage
- **`main.py`**: FastAPI application with REST API endpoints

## 🚀 Getting Started

### Prerequisites

- **Python**: 3.11 or higher
- **pip**: Latest version
- **Firestore**: Google Cloud project with Firestore enabled
- **API Keys**:
  - API-Football API key ([get one here](https://www.api-football.com/))
  - Google Gemini API key ([get one here](https://ai.google.dev/))

### Local Development Setup

1. **Create a virtual environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. **Set up environment variables**:
   
   Create a `.env` file in the `backend/` directory:
   ```bash
   # API Keys
   API_FOOTBALL_KEY=your_api_football_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Firestore Configuration
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
   FIRESTORE_PROJECT_ID=your-firebase-project-id
   
   # Optional: Cache settings
   CACHE_TTL_HOURS=24
   ```

4. **Run tests**:
   ```bash
   pytest
   
   # With coverage report
   pytest --cov=src --cov-report=html
   ```

5. **Run the server locally**:
   ```bash
   uvicorn src.main:app --reload
   
   # Server will start at http://localhost:8000
   ```

6. **Test the API**:
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # Trigger prediction update
   curl -X POST http://localhost:8000/api/update-predictions
   ```

## 📡 API Endpoints

### `GET /health`

Health check endpoint for monitoring and load balancers.

**Response**:
```json
{
  "status": "ok",
  "firestore": "ok",
  "cache_size": 48,
  "timestamp": "2026-06-11T10:00:00Z"
}
```

### `POST /api/update-predictions`

Triggers the full prediction pipeline:
1. Load tournament structure from Firestore
2. Calculate group standings using FIFA rules
3. Fetch team statistics from API-Football (with caching)
4. Generate AI predictions using Gemini
5. Resolve knockout bracket matchups
6. Publish predictions to Firestore

**Response**:
```json
{
  "status": "success",
  "updated_at": "2026-06-11T10:00:00Z",
  "predictions_generated": 104,
  "errors": []
}
```

**Error Response** (500):
```json
{
  "status": "error",
  "message": "Prediction pipeline failed",
  "errors": ["API-Football rate limit exceeded"]
}
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `API_FOOTBALL_KEY` | Yes | API-Football API key | - |
| `GEMINI_API_KEY` | Yes | Google Gemini API key | - |
| `FIRESTORE_PROJECT_ID` | Yes | Firebase project ID | - |
| `GOOGLE_APPLICATION_CREDENTIALS` | Yes | Path to service account JSON | - |
| `CACHE_TTL_HOURS` | No | Cache expiration time | 24 |

### API Rate Limiting

**API-Football**:
- Free tier: 100 requests/day
- Rate limit: 0.5 second delay between requests
- Retry strategy: Exponential backoff (1s, 2s, 4s) on 429/5xx errors
- **Caching**: 24-hour TTL on team statistics to minimize API calls

**Gemini AI**:
- Retry strategy: Max 1 retry (2 total attempts)
- Fallback: Rule-based predictions if Gemini fails twice
- Cost optimization: Use `response_mime_type: 'application/json'` for stable parsing

### Firestore Schema

**Main Document** (Hot Data):
- Path: `predictions/latest`
- Contents: Groups, bracket, AI summary, favorites, dark horses
- Max size: Keep under 1MB (Firestore limit)

**Sub-collections** (Cold Data):
- Path: `matches/{match_id}/history/{timestamp}`
- Purpose: Historical prediction changes
- Optimization: Diff check before writing (only save if prediction changed)

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/test_fifa_engine.py

# With coverage
pytest --cov=src --cov-report=html

# Integration tests only
pytest tests/test_integration.py
```

### Test Coverage

- **Minimum**: 80% (enforced)
- **Current**: View `htmlcov/index.html` after running coverage

### Test Structure

- **Unit Tests**: `test_*.py` for each module
- **Integration Tests**: `test_integration.py` for full pipeline
- **TDD Approach**: Tests created before implementation

## 🐳 Docker Deployment

### Build Docker Image

```bash
docker build -t vmkula-backend .
```

### Run Docker Container

```bash
docker run -p 8080:8080 \
  -e API_FOOTBALL_KEY=your_key \
  -e GEMINI_API_KEY=your_key \
  -e FIRESTORE_PROJECT_ID=your_project \
  -v /path/to/service-account.json:/app/service-account.json \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/service-account.json \
  vmkula-backend
```

### Deploy to Cloud Run

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for full deployment instructions.

**Quick Deploy**:
```bash
# Build and push to Google Container Registry
gcloud builds submit --config=cloudbuild.yaml

# Deploy to Cloud Run
gcloud run deploy vmkula-backend \
  --image=gcr.io/[PROJECT_ID]/vmkula-backend \
  --platform=managed \
  --region=us-east4 \
  --allow-unauthenticated
```

## ⚙️ Cloud Scheduler

The backend is triggered daily at 10:00 AM UTC by Google Cloud Scheduler.

**Configuration**: See `scheduler.yaml`

**Manual Trigger**:
```bash
gcloud scheduler jobs run vmkula-daily-update --location=us-east4
```

## 🛠️ Troubleshooting

### Common Errors

**1. "API-Football rate limit exceeded"**
- **Cause**: Free tier limit (100 requests/day) exceeded
- **Solution**: Wait 24 hours or upgrade to paid tier
- **Development**: Use cached data from `backend/cache/` directory

**2. "Gemini API error: 503 Service Unavailable"**
- **Cause**: Gemini service temporary unavailability
- **Solution**: Retry triggered automatically (max 1 retry)
- **Fallback**: Rule-based predictions used after 2 failures

**3. "Firestore permission denied"**
- **Cause**: Service account lacks Firestore permissions
- **Solution**: Grant `Cloud Datastore User` role to service account
  ```bash
  gcloud projects add-iam-policy-binding [PROJECT_ID] \
    --member=serviceAccount:[SERVICE_ACCOUNT] \
    --role=roles/datastore.user
  ```

**4. "Test environment variable validation failed"**
- **Cause**: Tests run without `.env` file
- **Solution**: Tests automatically use default values when pytest is detected
- **Note**: This is expected behavior - no action needed

### Clear Cache

```bash
# Delete all cached team statistics
rm -rf backend/cache/*.json

# Cache will be rebuilt on next prediction update
```

### View Logs

**Local Development**:
```bash
# Logs are printed to stdout
uvicorn src.main:app --reload
```

**Cloud Run**:
```bash
# View recent logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50 --format=json

# Stream logs in real-time
gcloud logging tail "resource.type=cloud_run_revision"
```

## 📊 Performance

### Execution Time Breakdown

Based on typical execution with cache hits:

| Component | Time | Notes |
|-----------|------|-------|
| SQLite queries | < 1 second | All tournament structure |
| API-Football fetches (48 teams) | ~24 seconds | With 0.5s delay (first run) |
| API-Football fetches (cached) | < 1 second | Subsequent runs within 24h |
| FIFA engine calculations | < 5 seconds | Standings + bracket |
| Gemini AI predictions (104 matches) | 2-3 minutes | Rate limited by AI API |
| Firestore writes | < 5 seconds | Main doc + diffs |
| **Total (first run)** | ~3-4 minutes | Cold cache |
| **Total (cached)** | ~2-3 minutes | Warm cache |

### Cloud Run Configuration

- **Memory**: 512MB
- **CPU**: 1
- **Timeout**: 300s (5 minutes)
- **Concurrency**: 10
- **Min instances**: 0 (scale to zero)
- **Max instances**: 5

## 🧩 FIFA Rules Implementation

### Tiebreaker Sequence

When teams have equal points in group standings:

1. **Goal Difference** (GD)
2. **Goals Scored**
3. **Head-to-Head** (if applicable)
4. **Fair Play Points** (calculated from cards)
5. **Deterministic Seed** (hash-based, prevents flickering)

### Fair Play Points

- Yellow card: -1 point
- Second yellow / Indirect red: -3 points
- Direct red card: -4 points

### Third-Place Qualification

- Extract all 3rd-place teams from 12 groups
- Sort by same criteria as group standings
- Select top 8 teams for Round of 32

## 📚 Additional Documentation

- **API Contracts**: See `docs/api.md`
- **Data Model**: See `docs/data-model.md`
- **Deployment Guide**: See `DEPLOYMENT.md`
- **Project Constitution**: See `../RULES.md`

## 🔗 Related Projects

- **Frontend**: `../frontend/` - Next.js web application
- **POC**: `../poc/` - Original proof of concept

## 📝 License

See `../LICENSE` for details.
