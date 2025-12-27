# Backend API Documentation

REST API reference for the World Cup 2026 prediction backend.

## Base URL

**Development**: `http://localhost:8000`  
**Production**: `https://vmkula-backend-[hash].a.run.app`

## Authentication

### Development
No authentication required for local development.

### Production (Cloud Run)
- **Method**: Cloud IAM authentication
- **Headers**: `Authorization: Bearer [CLOUD_RUN_TOKEN]`
- **Service Account**: Requires `roles/run.invoker` permission

**Get Token (for testing)**:
```bash
gcloud auth print-identity-token
```

**Example Request**:
```bash
curl -X POST https://vmkula-backend-[hash].a.run.app/api/update-predictions \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

## Endpoints

### 1. Health Check

**Endpoint**: `GET /health`  
**Purpose**: Verify system health and component status  
**Authentication**: None required

**Response** (200 OK):
```json
{
  "status": "healthy",
  "firestore": "ok",
  "teams_count": 48,
  "cache_size": 48,
  "timestamp": "2026-06-11T10:00:00Z"
}
```

**Response Fields**:
- `status`: Overall system status (`healthy`, `degraded`, `unhealthy`)
- `firestore`: Firestore connection status (`ok`, `error`)
- `teams_count`: Number of teams loaded from Firestore
- `cache_size`: Number of cached API-Football response files
- `timestamp`: Server timestamp (ISO8601)

**Example Request**:
```bash
curl http://localhost:8000/health
```

---

### 2. Update Tournament Structure

**Endpoint**: `POST /api/update-tournament`  
**Purpose**: Load tournament structure (groups, teams, matches) without AI predictions  
**Authentication**: Cloud IAM (production), None (development)

**Pipeline Steps**:
1. Load teams and matches from Firestore
2. Calculate group standings using FIFA rules
3. Rank third-place teams for knockout qualification
4. Resolve knockout bracket matchups
5. Publish tournament snapshot to Firestore (without predictions)

**Response** (200 OK):
```json
{
  "status": "success",
  "updated_at": "2026-06-11T10:00:00Z",
  "groups_calculated": 12,
  "bracket_matches_resolved": 32,
  "elapsed_seconds": 5.2,
  "errors": null
}
```

**Response** (500 Internal Server Error):
```json
{
  "status": "error",
  "message": "Tournament update failed: Firestore connection timeout",
  "errors": ["Failed to load teams from Firestore"]
}
```

**Response Fields**:
- `status`: `success`, `partial_success`, or `error`
- `updated_at`: Timestamp when update started (ISO8601)
- `groups_calculated`: Number of group standings calculated
- `bracket_matches_resolved`: Number of knockout matches resolved
- `elapsed_seconds`: Total pipeline execution time
- `errors`: Array of error messages (null if no errors)

**Example Request**:
```bash
# Development
curl -X POST http://localhost:8000/api/update-tournament

# Production
curl -X POST https://vmkula-backend-[hash].a.run.app/api/update-tournament \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

**Notes**:
- Fast operation (~5 seconds) - no AI predictions generated
- Should be run BEFORE `/api/update-predictions`
- Updates `predictions/latest` document with tournament structure only

---

### 3. Update Predictions

**Endpoint**: `POST /api/update-predictions`  
**Purpose**: Generate AI predictions for all matches  
**Authentication**: Cloud IAM (production), None (development)

**Pipeline Steps**:
1. Load existing tournament data from Firestore
2. Fetch team statistics from API-Football (with 24h caching)
3. Generate AI predictions using Gemini 3.0 Pro
4. Update Firestore with predictions (diff-based updates)

**Response** (200 OK):
```json
{
  "status": "success",
  "updated_at": "2026-06-11T10:00:00Z",
  "predictions_generated": 104,
  "gemini_success": 98,
  "gemini_fallback": 6,
  "firestore_cache_hits": 45,
  "firestore_cache_misses": 3,
  "predictions_cached": 80,
  "predictions_regenerated": 24,
  "elapsed_seconds": 125.5,
  "errors": null,
  "warnings": null
}
```

**Response** (400 Bad Request):
```json
{
  "status": "error",
  "detail": "No tournament data found. Run /api/update-tournament first."
}
```

**Response** (500 Internal Server Error):
```json
{
  "status": "error",
  "detail": "Prediction pipeline failed: API-Football rate limit exceeded",
  "errors": ["Failed to fetch stats for Brazil: 429 Too Many Requests"]
}
```

**Response Fields**:
- `status`: `success`, `partial_success`, or `error`
- `updated_at`: Timestamp when update started (ISO8601)
- `predictions_generated`: Total number of predictions generated
- `gemini_success`: Count of successful Gemini AI predictions
- `gemini_fallback`: Count of rule-based fallback predictions
- `firestore_cache_hits`: Team stats loaded from Firestore cache
- `firestore_cache_misses`: Team stats fetched fresh from API-Football
- `predictions_cached`: Predictions reused from cache (no regeneration needed)
- `predictions_regenerated`: Predictions regenerated due to stats changes
- `elapsed_seconds`: Total pipeline execution time
- `errors`: Array of error messages (null if no errors)
- `warnings`: Array of warning messages (null if no warnings)

**Example Request**:
```bash
# Development
curl -X POST http://localhost:8000/api/update-predictions

# Production (Cloud Scheduler triggers this daily)
curl -X POST https://vmkula-backend-[hash].a.run.app/api/update-predictions \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

**Notes**:
- Slow operation (~2-3 minutes) - AI predictions for 104 matches
- Requires `/api/update-tournament` to be run first
- Smart caching: Only regenerates predictions when team stats change
- Updates `predictions/latest` document and `predictions` array

---

### 4. Sync Match Flags

**Endpoint**: `POST /api/sync-match-flags`  
**Purpose**: Sync `has_real_data` flags from predictions to matches array  
**Authentication**: Cloud IAM (production), None (development)

**Pipeline Steps**:
1. Load existing snapshot from Firestore
2. Extract `has_real_data` flags from predictions array
3. Update matches array with flags
4. Publish updated snapshot to Firestore

**Response** (200 OK):
```json
{
  "status": "success",
  "matches_updated": 48,
  "total_predictions": 104
}
```

**Response** (404 Not Found):
```json
{
  "detail": "No predictions found. Run /api/update-predictions first."
}
```

**Response Fields**:
- `status`: `success` or `error`
- `matches_updated`: Number of matches with updated flags
- `total_predictions`: Total predictions in snapshot

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/sync-match-flags
```

**Notes**:
- Lightweight operation (<1 second)
- Does NOT regenerate predictions
- Useful for fixing data transformation issues

---

## Rate Limiting

### API-Football
- **Free Tier**: 100 requests/day
- **Rate Limit**: 0.5 second delay between requests (enforced in `data_aggregator.py`)
- **Retry Strategy**: Exponential backoff (1s, 2s, 4s) on 429/5xx errors
- **Caching**: 24-hour TTL on team statistics (Firestore-based)

### Gemini AI
- **Retry Strategy**: Max 1 retry (2 total attempts per prediction)
- **Timeout**: 30 seconds per prediction
- **Fallback**: Rule-based predictions if Gemini fails twice
- **Cost Optimization**: Use `response_mime_type: 'application/json'` for stable parsing

## Error Handling

### Common Error Codes

**400 Bad Request**:
- Missing prerequisites (e.g., `/api/update-tournament` not run first)
- Invalid request parameters

**401 Unauthorized** (Production only):
- Missing or invalid `Authorization` header
- Service account lacks `roles/run.invoker` permission

**429 Too Many Requests**:
- API-Football rate limit exceeded
- Wait 24 hours or upgrade to paid tier

**500 Internal Server Error**:
- Firestore connection timeout
- Gemini AI service unavailable
- Unexpected pipeline failures

**503 Service Unavailable**:
- Cloud Run service not available
- Backend container startup failure

### Error Response Format

All errors follow FastAPI's standard error format:
```json
{
  "detail": "Human-readable error message"
}
```

For pipeline errors, additional context is provided:
```json
{
  "status": "error",
  "detail": "Prediction pipeline failed: API-Football rate limit exceeded",
  "errors": [
    "Failed to fetch stats for Brazil: 429 Too Many Requests",
    "Failed to fetch stats for Argentina: 429 Too Many Requests"
  ]
}
```

## Request Examples

### Using curl

**Health Check**:
```bash
curl http://localhost:8000/health
```

**Update Tournament**:
```bash
curl -X POST http://localhost:8000/api/update-tournament
```

**Update Predictions**:
```bash
curl -X POST http://localhost:8000/api/update-predictions
```

**Production with IAM Auth**:
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -X POST https://vmkula-backend-[hash].a.run.app/api/update-predictions \
  -H "Authorization: Bearer $TOKEN"
```

### Using Python

```python
import requests

# Development
response = requests.post('http://localhost:8000/api/update-predictions')
print(response.json())

# Production
import subprocess

token = subprocess.check_output(['gcloud', 'auth', 'print-identity-token']).decode().strip()
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'https://vmkula-backend-[hash].a.run.app/api/update-predictions',
    headers=headers
)
print(response.json())
```

### Using JavaScript (Frontend)

```javascript
// Trigger backend refresh (fire-and-forget)
const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

fetch(`${backendUrl}/api/update-tournament`, {
  method: 'POST',
})
  .then(response => response.json())
  .then(data => console.log('Update triggered:', data))
  .catch(error => console.error('Update failed:', error))
```

## Cloud Scheduler Configuration

**Job Name**: `vmkula-daily-update`  
**Schedule**: `0 10 * * *` (Daily at 10:00 AM UTC)  
**Target**: Cloud Run service (`vmkula-backend`)  
**Endpoint**: `POST /api/update-predictions`  
**Authentication**: Service account with `roles/run.invoker`

**Manual Trigger**:
```bash
gcloud scheduler jobs run vmkula-daily-update --location=us-east4
```

**View Scheduler Logs**:
```bash
gcloud logging read "resource.type=cloud_scheduler_job" --limit=10
```

## OpenAPI Specification

The backend provides an auto-generated OpenAPI spec (Swagger UI):

**Development**: `http://localhost:8000/docs`  
**Production**: `https://vmkula-backend-[hash].a.run.app/docs`

**Interactive Testing**:
1. Navigate to `/docs` endpoint
2. Expand endpoint (e.g., `POST /api/update-predictions`)
3. Click "Try it out"
4. Execute request and view response

## Monitoring & Logs

### Cloud Run Logs

**View Recent Logs**:
```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit=50 \
  --format=json
```

**Stream Logs in Real-Time**:
```bash
gcloud logging tail "resource.type=cloud_run_revision"
```

**Filter by Endpoint**:
```bash
gcloud logging read "resource.type=cloud_run_revision AND textPayload:'/api/update-predictions'" \
  --limit=20
```

### Request Tracing

All requests include a unique `request_id` in logs for debugging:

```
2026-06-11T10:00:00.123Z - src.main - INFO - [a1b2c3d4] Request started: POST /api/update-predictions
2026-06-11T10:02:15.456Z - src.main - INFO - [a1b2c3d4] Request completed: 200
```

**Find Logs for Specific Request**:
```bash
gcloud logging read "textPayload:a1b2c3d4" --limit=100
```

## Related Documentation

- **Backend Setup**: `../README.md` - Development setup and deployment
- **Data Model**: `data-model.md` - Firestore schema and entities
- **Deployment Guide**: `../DEPLOYMENT.md` - Cloud Run deployment instructions
- **Frontend Integration**: `../../frontend/README.md` - How frontend consumes API
