# GitHub Secrets Setup Guide

## Issue
The GitHub Actions workflows are failing because the required secrets are not configured in your repository.

Error: `the GitHub Action workflow must specify exactly one of "workload_identity_provider" or "credentials_json"`

## Option 1: Service Account JSON (Quick Setup)

### 1. Create/Download Service Account Keys

#### For Backend (GCP):
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project (vmkula)
3. Go to **IAM & Admin → Service Accounts**
4. Find or create a service account with these roles:
   - Cloud Run Admin
   - Cloud Build Editor
   - Service Account User
5. Click **Keys → Add Key → Create New Key → JSON**
6. Save the JSON file securely

#### For Frontend (Firebase):
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project (vmkula)
3. Go to **Project Settings → Service Accounts**
4. Click **Generate New Private Key**
5. Save the JSON file securely

### 2. Add Secrets to GitHub

1. Go to your GitHub repository: `https://github.com/YOUR_USERNAME/vmkula`
2. Click **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `GCP_SA_KEY` | Contents of GCP service account JSON | For backend deployment |
| `GCP_PROJECT_ID` | `vmkula` (or your GCP project ID) | Google Cloud project ID |
| `FIREBASE_SERVICE_ACCOUNT` | Contents of Firebase service account JSON | For frontend deployment |
| `FIREBASE_PROJECT_ID` | `vmkula` | Firebase project ID |

**Important**: When pasting the JSON, paste the entire file content including curly braces.

### 3. Test the Deployment

Push a change to trigger the workflow:
```bash
git commit --allow-empty -m "Test deployment"
git push origin main
```

---

## Option 2: Workload Identity Federation (Recommended - No Secrets!)

This is more secure because it doesn't store long-lived credentials.

### 1. Set Up Workload Identity Pool

Run these commands in Google Cloud Shell or locally with `gcloud`:

```bash
# Set your project ID
export PROJECT_ID="vmkula"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export GITHUB_REPO="YOUR_GITHUB_USERNAME/vmkula"  # Replace with your repo

# Create Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create Service Account (or use existing)
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Service Account" \
  --project="${PROJECT_ID}"

# Grant necessary roles
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/cloudbuild.builds.editor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Allow GitHub Actions to impersonate service account
gcloud iam service-accounts add-iam-policy-binding \
  "github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"

# Get the Workload Identity Provider name
echo "Add this as WORKLOAD_IDENTITY_PROVIDER secret:"
echo "projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/providers/github-provider"

echo "Add this as SERVICE_ACCOUNT secret:"
echo "github-actions@${PROJECT_ID}.iam.gserviceaccount.com"
```

### 2. Add GitHub Secrets

Add only these secrets (no JSON keys needed!):

| Secret Name | Value | Example |
|-------------|-------|---------|
| `WORKLOAD_IDENTITY_PROVIDER` | From gcloud command output | `projects/123456789/locations/global/workloadIdentityPools/github-pool/providers/github-provider` |
| `SERVICE_ACCOUNT` | Your service account email | `github-actions@vmkula.iam.gserviceaccount.com` |
| `GCP_PROJECT_ID` | Your GCP project ID | `vmkula` |
| `FIREBASE_PROJECT_ID` | Your Firebase project ID | `vmkula` |

**Note**: Both workflows (backend and frontend) now use the same Workload Identity Federation setup. No service account JSON keys needed!

### 3. Update Workflow Files

I'll provide updated workflow files in the next step.

---

## Quick Fix (Use Option 1 for Now)

For immediate deployment, use **Option 1** - it's faster to set up. You can migrate to Option 2 later for better security.

## Verification

After adding secrets, check:
1. Go to GitHub repo → Settings → Secrets and variables → Actions
2. Verify all secrets are listed (values will be hidden)
3. Push a change to trigger deployment
4. Check Actions tab for deployment status
