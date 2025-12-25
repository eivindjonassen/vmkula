# Backend Deployment Guide

This guide covers deploying the vmkula backend to Google Cloud Run.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **APIs Enabled**:
   - Cloud Run API
   - Cloud Build API
   - Container Registry API
   - Secret Manager API
   - Cloud Scheduler API (for T043)

```bash
gcloud services enable run.googleapis.com \
  cloudbuild.googleapis.com \
  containerregistry.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com
```

## Setup Steps

### 1. Set Project Variables

```bash
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export SERVICE_NAME="vmkula-backend"
export SERVICE_ACCOUNT="${SERVICE_NAME}-sa"
```

### 2. Create Service Account

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create ${SERVICE_ACCOUNT} \
  --display-name="vmkula Backend Service Account" \
  --project=${PROJECT_ID}

# Grant Firestore write permissions
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Grant Secret Manager access (to read API keys)
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Create Secrets in Secret Manager

```bash
# Create GEMINI_API_KEY secret
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=${PROJECT_ID}

# Create API_FOOTBALL_KEY secret
echo -n "your-api-football-key" | gcloud secrets create API_FOOTBALL_KEY \
  --data-file=- \
  --replication-policy="automatic" \
  --project=${PROJECT_ID}

# Create FIRESTORE_PROJECT_ID secret
echo -n "${PROJECT_ID}" | gcloud secrets create FIRESTORE_PROJECT_ID \
  --data-file=- \
  --replication-policy="automatic" \
  --project=${PROJECT_ID}
```

### 4. Deploy Using Cloud Build (Recommended)

```bash
# Submit build from repository root
gcloud builds submit --config=backend/cloudbuild.yaml --project=${PROJECT_ID}
```

This will:
1. Build Docker image
2. Push to Container Registry
3. Deploy to Cloud Run
4. Configure service with secrets and environment variables

### 5. Manual Deployment (Alternative)

```bash
# Build Docker image locally
cd backend
docker build -t gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest .

# Push to Container Registry
docker push gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest

# Deploy to Cloud Run
gcloud run deploy ${SERVICE_NAME} \
  --image=gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest \
  --region=${REGION} \
  --platform=managed \
  --allow-unauthenticated \
  --memory=512Mi \
  --cpu=1 \
  --concurrency=10 \
  --min-instances=0 \
  --max-instances=5 \
  --timeout=300s \
  --set-env-vars=PYTHONUNBUFFERED=1 \
  --set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest,API_FOOTBALL_KEY=API_FOOTBALL_KEY:latest,FIRESTORE_PROJECT_ID=FIRESTORE_PROJECT_ID:latest \
  --service-account=${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com \
  --project=${PROJECT_ID}
```

## Verify Deployment

### 1. Check Service Health

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --format='value(status.url)' \
  --project=${PROJECT_ID})

echo "Service URL: ${SERVICE_URL}"

# Test health endpoint
curl ${SERVICE_URL}/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "firestore": "connected",
  "cache_size": 0
}
```

### 2. Trigger Prediction Update

```bash
# Call update-predictions endpoint
curl -X POST ${SERVICE_URL}/api/update-predictions
```

### 3. Monitor Logs

```bash
# View logs in real-time
gcloud run services logs tail ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_ID}
```

## Cost Optimization

**Free Tier Benefits**:
- Cloud Run: 2 million requests/month free
- Container Registry: 0.5 GB storage free
- Firestore: 1 GB storage, 50K reads/day free

**Configuration for Cost Savings**:
- `minInstances: 0` - Scale to zero when not in use
- `memory: 512Mi` - Minimum memory for Python FastAPI
- `timeout: 300s` - Allow time for AI calls but prevent runaway costs
- `maxInstances: 5` - Cap concurrent instances

**Expected Costs** (tournament active period):
- Cloud Run: ~$0-5/month (minimal traffic, scale to zero)
- API-Football: Free tier (100 req/day)
- Gemini AI: ~$0.10 per full prediction run (104 matches)

## Troubleshooting

### Build Fails

**Error**: `Cannot find worldcup2026.db`
- **Solution**: Ensure `worldcup2026.db` exists in `backend/` directory

**Error**: `Permission denied (Cloud Build)`
- **Solution**: Grant Cloud Build service account necessary permissions:
  ```bash
  PROJECT_NUMBER=$(gcloud projects describe ${PROJECT_ID} --format='value(projectNumber)')
  gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member=serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com \
    --role=roles/run.admin
  ```

### Deployment Fails

**Error**: `Secret not found`
- **Solution**: Create secrets in Secret Manager (see step 3)

**Error**: `Service account does not exist`
- **Solution**: Create service account (see step 2)

### Runtime Errors

**Error**: `Firestore permission denied`
- **Solution**: Grant `roles/datastore.user` to service account

**Error**: `Health check failed`
- **Solution**: Check logs for Python errors, verify database exists

## Rollback

```bash
# List revisions
gcloud run revisions list --service=${SERVICE_NAME} --region=${REGION}

# Rollback to previous revision
gcloud run services update-traffic ${SERVICE_NAME} \
  --region=${REGION} \
  --to-revisions=REVISION_NAME=100
```

## CI/CD with GitHub Actions

See `T046` for automated deployment via GitHub Actions.

## Next Steps

- **T043**: Set up Cloud Scheduler for daily updates
- **T046**: Configure GitHub Actions for automated deployments
- **T048**: Complete backend README documentation

---

**Last Updated**: 2025-12-26
