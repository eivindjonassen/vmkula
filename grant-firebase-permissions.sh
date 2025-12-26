#!/bin/bash
# Grant Firebase Hosting permissions to the service account

export PROJECT_ID="vmkula"
export SERVICE_ACCOUNT="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

echo "Granting Firebase Hosting Admin role to ${SERVICE_ACCOUNT}..."

# Grant Firebase Hosting Admin role
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/firebasehosting.admin"

# Grant Firebase Admin role (broader permissions if needed)
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT}" \
  --role="roles/firebase.admin"

echo "✅ Permissions granted successfully!"
echo ""
echo "Service account ${SERVICE_ACCOUNT} now has:"
echo "  - Firebase Hosting Admin (roles/firebasehosting.admin)"
echo "  - Firebase Admin (roles/firebase.admin)"
