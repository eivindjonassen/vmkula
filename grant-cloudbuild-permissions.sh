#!/bin/bash
# Grant Cloud Build permissions to GitHub Actions service account

export PROJECT_ID="vmkula"
export SERVICE_ACCOUNT="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Granting Cloud Build permissions to ${SERVICE_ACCOUNT}..."

# 1. Service Usage Consumer - allows using services
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/serviceusage.serviceUsageConsumer"

# 2. Storage Admin - access to Cloud Build bucket
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/storage.admin"

# 3. Cloud Build Service Account - run Cloud Build
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/cloudbuild.builds.builder"

# 4. Logs Writer - write build logs
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/logging.logWriter"

echo ""
echo "✅ Cloud Build permissions granted successfully!"
echo ""
echo "Service account ${SERVICE_ACCOUNT} now has:"
echo "  - Service Usage Consumer (roles/serviceusage.serviceUsageConsumer)"
echo "  - Storage Admin (roles/storage.admin)"
echo "  - Cloud Build Builder (roles/cloudbuild.builds.builder)"
echo "  - Logging Log Writer (roles/logging.logWriter)"
echo ""
echo "You can now trigger GitHub Actions deployment!"
