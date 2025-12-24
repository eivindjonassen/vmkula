#!/usr/bin/env bash
# Bifrost Session Memory Migration Script
# Migrates from old single session format to new per-feature session format
#
# Usage:
#   migrate-session-memory.sh [feature-name]
#
# If feature-name not provided, auto-detects from .bifrost/active-workflow marker
#
# Process:
#   1. Detect or validate feature name
#   2. Copy .bifrost/memory/session.md → specs/[feature-name]/session.md
#   3. Verify Active Focus feature name matches detected feature
#   4. Extract cross-feature learnings to project session format
#   5. Archive old session as .bifrost/memory/session.md.backup-[date]
#   6. Provide summary report
#
# Exit codes:
#   0 = success
#   1 = no session to migrate or workflow marker not found
#   2 = feature name mismatch (Active Focus doesn't match detected/provided feature)
#   3 = template not found or directory creation failed

set -euo pipefail

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Helper function for consistent error reporting
error_exit() {
    local message="$1"
    local exit_code="${2:-1}"
    echo -e "${RED}❌ ERROR: $message${NC}" >&2
    exit "$exit_code"
}

# Helper function for info messages
info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Helper function for success messages
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

# Helper function for warning messages
warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Get feature name from argument or active-workflow marker
FEATURE_NAME="${1:-}"

if [[ -z "$FEATURE_NAME" ]]; then
    info "No feature name provided, auto-detecting from .bifrost/active-workflow..."

    if [[ ! -f ".bifrost/active-workflow" ]]; then
        error_exit "No .bifrost/active-workflow marker found. Please provide feature-name argument." 1
    fi

    # Parse feature name from workflow marker format: specs/[feature-name]:phase|completed
    WORKFLOW_MARKER=$(cat .bifrost/active-workflow)
    FEATURE_NAME=$(echo "$WORKFLOW_MARKER" | sed -E 's|^specs/([^:]+):.*|\1|')

    if [[ -z "$FEATURE_NAME" ]]; then
        error_exit "Could not parse feature name from workflow marker: $WORKFLOW_MARKER" 1
    fi

    info "Auto-detected feature name: $FEATURE_NAME"
else
    info "Using provided feature name: $FEATURE_NAME"
fi

# Validate source session file exists
OLD_SESSION=".bifrost/memory/session.md"
if [[ ! -f "$OLD_SESSION" ]]; then
    error_exit "No session file found at $OLD_SESSION. Nothing to migrate." 1
fi

# Extract feature name from Active Focus section in old session file
info "Verifying Active Focus feature name in session file..."
ACTIVE_FEATURE=$(grep -A 3 '^## 🎯 Active Focus' "$OLD_SESSION" | grep '\*\*Feature\*\*:' | sed -E 's/^-? ?\*\*Feature\*\*: ?//' | xargs)

if [[ -z "$ACTIVE_FEATURE" ]]; then
    warning "Could not extract Active Focus feature from session file. Proceeding with provided/detected feature: $FEATURE_NAME"
elif [[ "$ACTIVE_FEATURE" != "$FEATURE_NAME" ]]; then
    error_exit "Feature name mismatch! Active Focus shows '$ACTIVE_FEATURE' but detected/provided feature is '$FEATURE_NAME'. Please verify the correct feature name." 2
else
    success "Active Focus verification passed: $ACTIVE_FEATURE"
fi

# Create target directory if it doesn't exist
TARGET_DIR="specs/$FEATURE_NAME"
if [[ ! -d "$TARGET_DIR" ]]; then
    info "Creating directory: $TARGET_DIR"
    mkdir -p "$TARGET_DIR" || error_exit "Failed to create directory: $TARGET_DIR" 3
fi

# Copy session file to feature-specific location
NEW_SESSION="$TARGET_DIR/session.md"
info "Copying $OLD_SESSION → $NEW_SESSION..."
cp "$OLD_SESSION" "$NEW_SESSION" || error_exit "Failed to copy session file to $NEW_SESSION" 3

success "Feature session created at: $NEW_SESSION"

# Extract cross-feature learnings to project session format
info "Extracting cross-feature learnings to project session format..."

PROJECT_SESSION=".bifrost/memory/session.md"
PROJECT_TEMPLATE=".bifrost/memory/project-session.md"

# Check if project session template exists
if [[ ! -f "$PROJECT_TEMPLATE" ]]; then
    error_exit "Project session template not found at $PROJECT_TEMPLATE. Please run bifrost-admin.py to sync latest templates from Bifrost repo." 3
fi

# Initialize project session from template if it doesn't exist yet
# (This would be the first migration, so we create the project session)
# For subsequent migrations, we'll append to existing project session
if [[ ! -f "$PROJECT_SESSION" ]] || [[ ! -s "$PROJECT_SESSION" ]]; then
    info "Initializing project session from template..."
    cp "$PROJECT_TEMPLATE" "$PROJECT_SESSION"
    success "Project session initialized at: $PROJECT_SESSION"
else
    info "Project session already exists (will be updated by rollup script)"
fi

# Archive old session file with timestamp
BACKUP_DATE=$(date +"%Y%m%d-%H%M%S")
BACKUP_FILE=".bifrost/memory/session.md.backup-$BACKUP_DATE"

info "Archiving old session file: $BACKUP_FILE"
mv "$OLD_SESSION" "$BACKUP_FILE" || error_exit "Failed to archive old session file" 3

success "Old session archived at: $BACKUP_FILE"

# Summary report
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ MIGRATION COMPLETE${NC}"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "📋 Summary:"
echo "  • Feature: $FEATURE_NAME"
echo "  • Feature session: $NEW_SESSION"
echo "  • Project session: $PROJECT_SESSION"
echo "  • Backup: $BACKUP_FILE"
echo ""
echo "📝 Next steps:"
echo "  1. Review migrated session file: $NEW_SESSION"
echo "  2. Run rollup script to extract learnings:"
echo "     .bifrost/scripts/rollup-session-learnings.sh $FEATURE_NAME"
echo "  3. Verify workflow commands now use feature-specific session path"
echo "  4. Clean up backup file after validation (if desired)"
echo ""
echo "═══════════════════════════════════════════════════════════════════"

exit 0
