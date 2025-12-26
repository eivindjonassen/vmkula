# ✅ vmkula GCP Setup Complete

**Date**: 2025-12-26  
**Status**: Ready for GitHub Actions Deployment

## What Was Fixed

### 1. ❌ Billing Not Enabled → ✅ Billing Enabled
- **Issue**: Cloud Build API couldn't be enabled without billing
- **Solution**: Enabled billing on vmkula project

### 2. ❌ APIs Not Enabled → ✅ APIs Enabled
Successfully enabled:
- ✅ Cloud Build API (`cloudbuild.googleapis.com`)
- ✅ Container Registry API (`containerregistry.googleapis.com`)
- ✅ Cloud Run API (`run.googleapis.com`)
- ✅ Secret Manager API (`secretmanager.googleapis.com`)
- ✅ Artifact Registry API (`artifactregistry.googleapis.com`)

### 3. ❌ Missing Permissions → ✅ All Permissions Granted

#### github-actions@vmkula.iam.gserviceaccount.com
- ✅ `roles/cloudbuild.builds.builder`
- ✅ `roles/cloudbuild.builds.editor`
- ✅ `roles/firebase.admin`
- ✅ `roles/firebasehosting.admin`
- ✅ `roles/iam.serviceAccountUser`
- ✅ `roles/logging.logWriter`
- ✅ `roles/run.admin`
- ✅ `roles/serviceusage.serviceUsageConsumer`
- ✅ `roles/storage.admin`

#### Cloud Build Service Account (647683442170@cloudbuild.gserviceaccount.com)
- ✅ `roles/run.admin`
- ✅ `roles/iam.serviceAccountUser`

#### Compute Engine Default SA (647683442170-compute@developer.gserviceaccount.com)
- ✅ `roles/storage.admin`
- ✅ `roles/logging.logWriter`

### 4. ✅ Cloud Build Test Successful
Ran test build that completed successfully:
```
ID: 18a22d61-d510-42e4-ab26-193e7a48ddcf
STATUS: SUCCESS
DURATION: 9s
```

## Project Configuration

**Project ID**: `vmkula`  
**Project Number**: `647683442170`  
**Region**: `us-central1`  
**Service Name**: `vmkula-backend`

## GitHub Actions Setup

### Required Secrets (Already Configured)
- ✅ `WORKLOAD_IDENTITY_PROVIDER`
- ✅ `SERVICE_ACCOUNT`
- ✅ `GCP_PROJECT_ID`

### Workflows Ready
- ✅ `.github/workflows/backend-deploy.yml` - Backend deployment
- ✅ `.github/workflows/frontend-deploy.yml` - Frontend deployment

## Next Steps

### 1. Configure Backend Secrets in Secret Manager

You still need to create these secrets for the backend to work:

```bash
# Set project
gcloud config set project vmkula

# Create GEMINI_API_KEY secret
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY \
  --data-file=- \
  --replication-policy="automatic"

# Create API_FOOTBALL_KEY secret
echo -n "your-api-football-key" | gcloud secrets create API_FOOTBALL_KEY \
  --data-file=- \
  --replication-policy="automatic"

# Create FIRESTORE_PROJECT_ID secret
echo -n "vmkula" | gcloud secrets create FIRESTORE_PROJECT_ID \
  --data-file=- \
  --replication-policy="automatic"
```

### 2. Create Backend Service Account

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create vmkula-backend-sa \
  --display-name="vmkula Backend Service Account"

# Grant Firestore permissions
gcloud projects add-iam-policy-binding vmkula \
  --member="serviceAccount:vmkula-backend-sa@vmkula.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding vmkula \
  --member="serviceAccount:vmkula-backend-sa@vmkula.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Trigger Deployment

Push to main branch or manually trigger:

```bash
# Empty commit to trigger deployment
git commit --allow-empty -m "Trigger deployment with fixed GCP setup"
git push origin main
```

Or manually trigger from GitHub Actions UI.

## Verification Commands

### Check Project Configuration
```bash
gcloud config get-value project
# Should output: vmkula
```

### Check Enabled APIs
```bash
gcloud services list --enabled --project=vmkula | grep -E "cloudbuild|container|run"
```

### Check Service Account Permissions
```bash
./check-cloudbuild-permissions.sh
```

### Test Cloud Build Locally
```bash
gcloud builds submit \
  --config=backend/cloudbuild.yaml \
  --project=vmkula \
  --substitutions=COMMIT_SHA=$(git rev-parse HEAD)
```

## Cost Estimate

With current configuration, expected costs:

**Free Tier Coverage**:
- Cloud Build: 120 build-minutes/day free ✅
- Cloud Run: 2M requests/month free ✅
- Container Registry: 0.5 GB storage free ✅
- Firestore: 1 GB storage, 50K reads/day free ✅

**Expected Monthly Cost**: $0-5 USD (should stay within free tier)

## Troubleshooting

### If GitHub Actions Still Fails

1. **Wait 1-2 minutes** - IAM permissions take time to propagate
2. **Check logs** - View build logs in GitHub Actions
3. **Verify secrets** - Ensure `GEMINI_API_KEY`, `API_FOOTBALL_KEY` are created in Secret Manager
4. **Check service account** - Verify `vmkula-backend-sa` exists

### Useful Scripts

- `./check-cloudbuild-permissions.sh` - Check permissions
- `./grant-cloudbuild-permissions.sh` - Grant missing permissions
- `./grant-firebase-permissions.sh` - Grant Firebase permissions

## Documentation References

- [Backend Deployment Guide](backend/DEPLOYMENT.md)
- [GitHub Secrets Setup](GITHUB_SECRETS_SETUP.md)
- [Fix Cloud Build Permissions](FIX_GITHUB_CLOUDBUILD_PERMISSIONS.md)

---

**Setup Status**: ✅ Complete  
**Ready for Deployment**: ✅ Yes  
**Next Action**: Create Secret Manager secrets and trigger deployment
