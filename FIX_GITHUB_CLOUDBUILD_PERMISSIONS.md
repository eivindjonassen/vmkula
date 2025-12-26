# Fix GitHub Actions Cloud Build Permissions

## Problem
GitHub Actions backend deployment is failing with:
```
ERROR: (gcloud.builds.submit) The user is forbidden from accessing the bucket [***_cloudbuild]. 
Please check your organization's policy or if the user has the "serviceusage.services.use" permission.
```

## Root Cause
The `github-actions` service account is missing these permissions:
- ❌ Service Usage Consumer
- ❌ Storage Admin (for Cloud Build bucket)
- ❌ Cloud Build Builder

## Solution

### Option 1: Run the Grant Script (Quick Fix)

```bash
./grant-cloudbuild-permissions.sh
```

This script grants:
- `roles/serviceusage.serviceUsageConsumer` - Use GCP services
- `roles/storage.admin` - Access Cloud Build bucket
- `roles/cloudbuild.builds.builder` - Run Cloud Build
- `roles/logging.logWriter` - Write build logs

### Option 2: Manual Commands

If you prefer to run commands manually:

```bash
export PROJECT_ID="vmkula"
export SERVICE_ACCOUNT="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant Service Usage Consumer
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/serviceusage.serviceUsageConsumer"

# Grant Storage Admin
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.admin"

# Grant Cloud Build Builder
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudbuild.builds.builder"

# Grant Logging Log Writer
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/logging.logWriter"
```

### Option 3: Security-Hardened (Least Privilege)

For tighter security, use more specific roles:

```bash
export PROJECT_ID="vmkula"
export SERVICE_ACCOUNT="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

# Service Usage Consumer (required)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/serviceusage.serviceUsageConsumer"

# Storage Object Admin (instead of Storage Admin)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.objectAdmin"

# Cloud Build Builder
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudbuild.builds.builder"

# Logs Writer
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/logging.logWriter"
```

## Verify Permissions

After granting permissions, verify:

```bash
# List all roles for the service account
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

Expected roles:
- `roles/cloudbuild.builds.builder`
- `roles/cloudbuild.builds.editor` (from original setup)
- `roles/iam.serviceAccountUser`
- `roles/logging.logWriter`
- `roles/run.admin`
- `roles/serviceusage.serviceUsageConsumer` ✅ NEW
- `roles/storage.admin` (or `storage.objectAdmin`) ✅ NEW

## Test Deployment

After granting permissions, retry the deployment:

### From GitHub Actions
Push a change or manually trigger the workflow:
```bash
git commit --allow-empty -m "Test Cloud Build permissions"
git push origin main
```

### Local Test (Optional)
```bash
gcloud builds submit \
  --config=backend/cloudbuild.yaml \
  --project=vmkula \
  --substitutions=COMMIT_SHA=$(git rev-parse HEAD)
```

## Troubleshooting

### Still Getting Permission Errors?

**Issue**: Permissions not propagating immediately
**Solution**: Wait 1-2 minutes for IAM changes to propagate

**Issue**: Organization policy blocking
**Solution**: Check organization policies:
```bash
gcloud resource-manager org-policies list --project=$PROJECT_ID
```

**Issue**: Service account doesn't exist
**Solution**: Verify service account exists:
```bash
gcloud iam service-accounts list --project=$PROJECT_ID | grep github-actions
```

### Alternative: Use Cloud Build Service Account

Instead of granting many permissions to `github-actions`, you can let Cloud Build use its own service account:

1. Remove `--service-account` from `cloudbuild.yaml` step 4
2. Grant Cloud Build SA the necessary permissions:
```bash
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/iam.serviceAccountUser"
```

## Summary

The issue occurs because GitHub Actions uses Workload Identity Federation to impersonate the `github-actions` service account, which then calls `gcloud builds submit`. Cloud Build requires:
1. **Service Usage Consumer** - to use the Cloud Build service
2. **Storage Admin/Object Admin** - to access the `{PROJECT}_cloudbuild` bucket where source code is staged
3. **Cloud Build Builder** - to create and manage builds

After running the grant script, your GitHub Actions should successfully deploy!

---

**Created**: 2025-12-26
**Status**: Ready to execute
