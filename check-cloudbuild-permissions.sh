#!/bin/bash
# Check Cloud Build permissions for GitHub Actions service account

export PROJECT_ID="vmkula"
export SERVICE_ACCOUNT="github-actions@${PROJECT_ID}.iam.gserviceaccount.com"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Checking Cloud Build Permissions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Project: ${PROJECT_ID}"
echo "Service Account: ${SERVICE_ACCOUNT}"
echo ""

# Check if service account exists
echo "1. Checking if service account exists..."
if gcloud iam service-accounts describe ${SERVICE_ACCOUNT} --project=${PROJECT_ID} &>/dev/null; then
    echo "   ✅ Service account exists"
else
    echo "   ❌ Service account NOT found"
    exit 1
fi
echo ""

# Get all roles for the service account
echo "2. Current IAM roles for service account:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
ROLES=$(gcloud projects get-iam-policy ${PROJECT_ID} \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:${SERVICE_ACCOUNT}" \
    --format="value(bindings.role)" | sort)

if [ -z "$ROLES" ]; then
    echo "   ⚠️  No roles found for service account"
else
    echo "$ROLES" | while read role; do
        echo "   • $role"
    done
fi
echo ""

# Check for required roles
echo "3. Required roles for Cloud Build:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

REQUIRED_ROLES=(
    "roles/serviceusage.serviceUsageConsumer"
    "roles/storage.admin|roles/storage.objectAdmin"
    "roles/cloudbuild.builds.builder|roles/cloudbuild.builds.editor"
    "roles/logging.logWriter"
)

REQUIRED_NAMES=(
    "Service Usage Consumer"
    "Storage Admin (or Object Admin)"
    "Cloud Build Builder (or Editor)"
    "Logging Log Writer"
)

ALL_GOOD=true

for i in "${!REQUIRED_ROLES[@]}"; do
    ROLE_PATTERN="${REQUIRED_ROLES[$i]}"
    ROLE_NAME="${REQUIRED_NAMES[$i]}"
    
    # Check if any of the alternative roles match
    if echo "$ROLES" | grep -qE "^(${ROLE_PATTERN})$"; then
        MATCHED_ROLE=$(echo "$ROLES" | grep -E "^(${ROLE_PATTERN})$" | head -1)
        echo "   ✅ $ROLE_NAME"
        echo "      → $MATCHED_ROLE"
    else
        echo "   ❌ $ROLE_NAME - MISSING"
        echo "      → Need one of: ${ROLE_PATTERN//|/ or }"
        ALL_GOOD=false
    fi
done
echo ""

# Check other important roles
echo "4. Other roles granted:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
OTHER_ROLES=$(echo "$ROLES" | grep -vE "(serviceusage|storage|cloudbuild|logging)")
if [ -z "$OTHER_ROLES" ]; then
    echo "   (none)"
else
    echo "$OTHER_ROLES" | while read role; do
        echo "   • $role"
    done
fi
echo ""

# Check specific permissions (testIamPermissions)
echo "5. Testing specific permissions:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PERMISSIONS=(
    "serviceusage.services.use"
    "storage.buckets.get"
    "storage.objects.create"
    "cloudbuild.builds.create"
    "cloudbuild.builds.get"
    "logging.logEntries.create"
)

for perm in "${PERMISSIONS[@]}"; do
    # Note: testIamPermissions requires impersonation or different approach
    # For now, we'll just show what should be testable
    echo "   → $perm (check via role grants above)"
done
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$ALL_GOOD" = true ]; then
    echo "✅ All required permissions are granted!"
    echo ""
    echo "Your GitHub Actions should be able to deploy successfully."
else
    echo "❌ Missing required permissions!"
    echo ""
    echo "Run this command to fix:"
    echo "  ./grant-cloudbuild-permissions.sh"
fi
echo ""
