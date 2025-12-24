#!/usr/bin/env bash
# Bifrost Session Learnings Rollup Script
# Extracts cross-feature learnings from feature session to project session
#
# Usage:
#   rollup-session-learnings.sh <feature-name>
#
# Process:
#   1. Read feature session from specs/[feature-name]/session.md
#   2. Extract: Architectural Decisions, Design Choices, Insights, Recovery Patterns, Technical Debt
#   3. Filter out feature-specific details (task IDs, file paths, implementation details)
#   4. Format with feature attribution tags: **[feature-name, YYYY-MM-DD]**:
#   5. Check for duplicates before appending (idempotent)
#   6. Write to project session at .bifrost/memory/session.md
#   7. Provide extraction summary
#
# Exit codes:
#   0 = success
#   1 = feature session not found
#   2 = no extractable learnings
#   3 = project session not writable

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

# Validate feature name argument
FEATURE_NAME="${1:-}"
if [[ -z "$FEATURE_NAME" ]]; then
    error_exit "Missing required argument: feature-name" 1
fi

info "Extracting learnings from feature: $FEATURE_NAME"

# Validate feature session file exists
FEATURE_SESSION="specs/$FEATURE_NAME/session.md"
if [[ ! -f "$FEATURE_SESSION" ]]; then
    error_exit "Feature session not found: $FEATURE_SESSION" 1
fi

# Validate project session file exists and is writable
PROJECT_SESSION=".bifrost/memory/session.md"
if [[ ! -f "$PROJECT_SESSION" ]]; then
    error_exit "Project session not found: $PROJECT_SESSION. Run migration script first." 3
fi

if [[ ! -w "$PROJECT_SESSION" ]]; then
    error_exit "Project session is not writable: $PROJECT_SESSION" 3
fi

# Current date for attribution tags
CURRENT_DATE=$(date +"%Y-%m-%d")
ATTRIBUTION_TAG="[$FEATURE_NAME, $CURRENT_DATE]"

# Counters for summary report
COUNT_ARCH_DECISIONS=0
COUNT_DESIGN_CHOICES=0
COUNT_INSIGHTS=0
COUNT_RECOVERY_PATTERNS=0
COUNT_TECH_DEBT=0
COUNT_CONVENTIONS=0
COUNT_FILTERED=0
COUNT_DUPLICATES=0

# Temporary files for extracted content
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

TEMP_ARCH="$TEMP_DIR/arch.txt"
TEMP_DESIGN="$TEMP_DIR/design.txt"
TEMP_INSIGHTS="$TEMP_DIR/insights.txt"
TEMP_RECOVERY="$TEMP_DIR/recovery.txt"
TEMP_DEBT="$TEMP_DIR/debt.txt"
TEMP_CONVENTIONS="$TEMP_DIR/conventions.txt"

# Helper function to check if content already exists in project session
is_duplicate() {
    local content="$1"
    local section_start="$2"

    # Extract first 50 characters for comparison (ignore attribution tag differences)
    local content_key=$(echo "$content" | sed -E 's/^\*\*\[.*\]: //' | head -c 50)

    # Search for similar content in the target section
    if grep -q "$content_key" "$PROJECT_SESSION"; then
        return 0  # Is duplicate
    else
        return 1  # Not duplicate
    fi
}

# Helper function to filter out feature-specific details
filter_feature_specifics() {
    local input="$1"

    # Filter patterns (return empty if any match):
    # - Task IDs (T001, T014, etc.)
    # - File paths (src/*, specs/*, etc.)
    # - Specific timestamps without context
    # - "Completed T..." or "Task T..." references

    if echo "$input" | grep -qE '(^|[^a-zA-Z])(T[0-9]{3})([^0-9]|$)'; then
        return 1  # Filter out
    fi

    if echo "$input" | grep -qE '^- .*\.(ts|js|go|py|md):'; then
        return 1  # Filter out file path bullets
    fi

    if echo "$input" | grep -qiE '(completed|finished|implemented) T[0-9]{3}'; then
        return 1  # Filter out task completion references
    fi

    return 0  # Keep it
}

info "Extracting Architectural Decisions..."
# Extract from "## 🧠 Key Decisions & Context" → "### Architectural Decisions"
if grep -q '### Architectural Decisions' "$FEATURE_SESSION"; then
    sed -n '/^### Architectural Decisions$/,/^###/p' "$FEATURE_SESSION" | \
        grep '^- ' | \
        while IFS= read -r line; do
            # Remove leading "- " and check if it should be filtered
            content=$(echo "$line" | sed 's/^- //')
            if filter_feature_specifics "$content"; then
                formatted="**$ATTRIBUTION_TAG**: $content"
                if ! is_duplicate "$formatted" "## 🏗️ Architectural Patterns"; then
                    echo "$formatted" >> "$TEMP_ARCH"
                    COUNT_ARCH_DECISIONS=$((COUNT_ARCH_DECISIONS + 1))
                else
                    COUNT_DUPLICATES=$((COUNT_DUPLICATES + 1))
                fi
            else
                COUNT_FILTERED=$((COUNT_FILTERED + 1))
            fi
        done || true
fi

info "Extracting Design Choices..."
# Extract from "### Design Choices"
if grep -q '### Design Choices' "$FEATURE_SESSION"; then
    sed -n '/^### Design Choices$/,/^###/p' "$FEATURE_SESSION" | \
        grep '^- ' | \
        while IFS= read -r line; do
            content=$(echo "$line" | sed 's/^- //')
            if filter_feature_specifics "$content"; then
                formatted="**$ATTRIBUTION_TAG**: $content"
                if ! is_duplicate "$formatted" "## 🏗️ Architectural Patterns"; then
                    echo "$formatted" >> "$TEMP_DESIGN"
                    COUNT_DESIGN_CHOICES=$((COUNT_DESIGN_CHOICES + 1))
                else
                    COUNT_DUPLICATES=$((COUNT_DUPLICATES + 1))
                fi
            else
                COUNT_FILTERED=$((COUNT_FILTERED + 1))
            fi
        done || true
fi

info "Extracting Insights & Learnings..."
# Extract from "## 💡 Insights & Learnings" - multiple subsections
if grep -q '## 💡 Insights & Learnings' "$FEATURE_SESSION"; then
    # Extract "What Worked Well"
    if grep -q '### What Worked Well' "$FEATURE_SESSION"; then
        sed -n '/^### What Worked Well$/,/^###/p' "$FEATURE_SESSION" | \
            grep '^- ' | \
            while IFS= read -r line; do
                content=$(echo "$line" | sed 's/^- //')
                if filter_feature_specifics "$content"; then
                    formatted="**$ATTRIBUTION_TAG**: $content"
                    if ! is_duplicate "$formatted" "## 📊 Workflow Improvements"; then
                        echo "$formatted" >> "$TEMP_INSIGHTS"
                        COUNT_INSIGHTS=$((COUNT_INSIGHTS + 1))
                    else
                        COUNT_DUPLICATES=$((COUNT_DUPLICATES + 1))
                    fi
                else
                    COUNT_FILTERED=$((COUNT_FILTERED + 1))
                fi
            done || true
    fi

    # Extract "Patterns Discovered" → Codebase Conventions
    if grep -q '### Patterns Discovered' "$FEATURE_SESSION"; then
        sed -n '/^### Patterns Discovered$/,/^###/p' "$FEATURE_SESSION" | \
            grep '^- ' | \
            while IFS= read -r line; do
                content=$(echo "$line" | sed 's/^- //')
                if filter_feature_specifics "$content"; then
                    formatted="**$ATTRIBUTION_TAG**: $content"
                    if ! is_duplicate "$formatted" "## 📜 Codebase Conventions"; then
                        echo "$formatted" >> "$TEMP_CONVENTIONS"
                        COUNT_CONVENTIONS=$((COUNT_CONVENTIONS + 1))
                    else
                        COUNT_DUPLICATES=$((COUNT_DUPLICATES + 1))
                    fi
                else
                    COUNT_FILTERED=$((COUNT_FILTERED + 1))
                fi
            done || true
    fi
fi

info "Extracting Recovery Patterns..."
# Extract from "### Recovery Patterns" (has special multi-line format)
if grep -q '### Recovery Patterns' "$FEATURE_SESSION"; then
    # Extract each recovery pattern block (starts with "**[Error Category]")
    sed -n '/^### Recovery Patterns$/,/^###/p' "$FEATURE_SESSION" | \
        awk '
            /^\*\*\[.*\]:/ {
                if (block != "") {
                    print block
                }
                block = $0
                next
            }
            /^  - / {
                if (block != "") {
                    block = block "\n" $0
                }
            }
            END {
                if (block != "") {
                    print block
                }
            }
        ' | \
        while IFS= read -r pattern_block; do
            # Check if pattern contains task IDs or overly specific implementation details
            if filter_feature_specifics "$pattern_block"; then
                # Add feature attribution to the pattern title
                formatted=$(echo "$pattern_block" | sed -E "s/^\*\*\[([^]]+)\]: /**[\1] - $ATTRIBUTION_TAG**: /")
                if ! is_duplicate "$formatted" "## 🔧 Error Recovery Patterns"; then
                    echo "$formatted" >> "$TEMP_RECOVERY"
                    COUNT_RECOVERY_PATTERNS=$((COUNT_RECOVERY_PATTERNS + 1))
                else
                    COUNT_DUPLICATES=$((COUNT_DUPLICATES + 1))
                fi
            else
                COUNT_FILTERED=$((COUNT_FILTERED + 1))
            fi
        done || true
fi

info "Extracting Technical Debt..."
# Extract from "### Technical Debt"
if grep -q '### Technical Debt' "$FEATURE_SESSION"; then
    sed -n '/^### Technical Debt$/,/^###/p' "$FEATURE_SESSION" | \
        grep '^- ' | \
        while IFS= read -r line; do
            content=$(echo "$line" | sed 's/^- //')
            if filter_feature_specifics "$content"; then
                formatted="**$ATTRIBUTION_TAG**: $content"
                if ! is_duplicate "$formatted" "## 💳 Technical Debt Registry"; then
                    echo "$formatted" >> "$TEMP_DEBT"
                    COUNT_TECH_DEBT=$((COUNT_TECH_DEBT + 1))
                else
                    COUNT_DUPLICATES=$((COUNT_DUPLICATES + 1))
                fi
            else
                COUNT_FILTERED=$((COUNT_FILTERED + 1))
            fi
        done || true
fi

# Calculate total extracted items
TOTAL_EXTRACTED=$((COUNT_ARCH_DECISIONS + COUNT_DESIGN_CHOICES + COUNT_INSIGHTS + COUNT_RECOVERY_PATTERNS + COUNT_TECH_DEBT + COUNT_CONVENTIONS))

if [[ $TOTAL_EXTRACTED -eq 0 ]]; then
    warning "No extractable learnings found (all filtered or duplicates)"
    echo ""
    echo "Summary:"
    echo "  • Filtered items: $COUNT_FILTERED (feature-specific details)"
    echo "  • Duplicate items: $COUNT_DUPLICATES (already in project session)"
    exit 2
fi

info "Appending learnings to project session..."

# Helper function to append content to a section
append_to_section() {
    local section_marker="$1"
    local temp_file="$2"

    if [[ -f "$temp_file" && -s "$temp_file" ]]; then
        # Find the section and append content after "Entries** (newest first):"
        # Use awk to find the section and insert after the entries marker
        awk -v section="$section_marker" -v content="$(cat "$temp_file")" '
            $0 ~ section { in_section = 1 }
            in_section && /\*\*Entries\*\* \(newest first\):/ {
                print
                print content
                in_section = 0
                next
            }
            { print }
        ' "$PROJECT_SESSION" > "$PROJECT_SESSION.tmp" && mv "$PROJECT_SESSION.tmp" "$PROJECT_SESSION"
    fi
}

# Append to each section
[[ -f "$TEMP_ARCH" ]] && append_to_section "## 🏗️ Architectural Patterns" "$TEMP_ARCH"
[[ -f "$TEMP_DESIGN" ]] && append_to_section "## 🏗️ Architectural Patterns" "$TEMP_DESIGN"
[[ -f "$TEMP_INSIGHTS" ]] && append_to_section "## 📊 Workflow Improvements" "$TEMP_INSIGHTS"
[[ -f "$TEMP_RECOVERY" ]] && append_to_section "## 🔧 Error Recovery Patterns" "$TEMP_RECOVERY"
[[ -f "$TEMP_DEBT" ]] && append_to_section "## 💳 Technical Debt Registry" "$TEMP_DEBT"
[[ -f "$TEMP_CONVENTIONS" ]] && append_to_section "## 📜 Codebase Conventions" "$TEMP_CONVENTIONS"

# Update Last Updated date in project session
sed -i.bak -E "s/^\*\*Last Updated\*\*: .*/\*\*Last Updated\*\*: $CURRENT_DATE/" "$PROJECT_SESSION" && rm -f "$PROJECT_SESSION.bak"

success "Learnings appended to project session"

# Summary report
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo -e "${GREEN}✅ ROLLUP COMPLETE${NC}"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "📋 Extraction Summary:"
echo "  • Feature: $FEATURE_NAME"
echo "  • Feature session: $FEATURE_SESSION"
echo "  • Project session: $PROJECT_SESSION"
echo ""
echo "📊 Extracted Learnings:"
echo "  • Architectural Decisions: $COUNT_ARCH_DECISIONS"
echo "  • Design Choices: $COUNT_DESIGN_CHOICES"
echo "  • Workflow Improvements: $COUNT_INSIGHTS"
echo "  • Recovery Patterns: $COUNT_RECOVERY_PATTERNS"
echo "  • Technical Debt: $COUNT_TECH_DEBT"
echo "  • Codebase Conventions: $COUNT_CONVENTIONS"
echo "  • ────────────────────────────"
echo "  • Total Extracted: $TOTAL_EXTRACTED"
echo ""
echo "🔍 Filtering Results:"
echo "  • Feature-specific items filtered: $COUNT_FILTERED"
echo "  • Duplicate items skipped: $COUNT_DUPLICATES"
echo ""
echo "📝 Next steps:"
echo "  1. Review extracted learnings in project session"
echo "  2. Use project session as reference for future features"
echo "  3. Run rollup after each feature completion for knowledge accumulation"
echo ""
echo "═══════════════════════════════════════════════════════════════════"

exit 0
