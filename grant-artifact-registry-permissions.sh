#!/bin/bash
# Grant Artifact Registry permissions to Cloud Build and GitHub Actions service accounts

export PROJECT_ID="vmkula"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
export CLOUDBUILD_SA="${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com"
export GITHUB_ACTIONS_SA="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Granting Artifact Registry permissions..."

# 1. Grant Artifact Registry Writer to Cloud Build Service Account
echo "Granting roles/artifactregistry.writer to ${CLOUDBUILD_SA}..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/artifactregistry.writer"

# 2. Grant Artifact Registry Writer to GitHub Actions Service Account (optional but helpful)
echo "Granting roles/artifactregistry.writer to ${GITHUB_ACTIONS_SA}..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${GITHUB_ACTIONS_SA}" \
  --role="roles/artifactregistry.writer"

# 3. Ensure Cloud Build SA has permission to use the backend service account
# The cloudbuild.yaml uses --service-account=vmkula-backend-sa@vmkula.iam.gserviceaccount.com
echo "Granting Service Account User to Cloud Build SA on backend-sa..."
gcloud iam service-accounts add-iam-policy-binding \
  vmkula-backend-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --member="serviceAccount:${CLOUDBUILD_SA}" \
  --role="roles/iam.serviceAccountUser"

echo ""
echo "✅ Permissions granted successfully!"
