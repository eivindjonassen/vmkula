#!/usr/bin/env bash
# validate-session-history.sh - Validate and optionally fix session history entries
# Usage: ./validate-session-history.sh <feature-name> [--fix]
#
# Purpose: Ensure session history maintains exactly 5 entries (or fewer)
# Returns: 0 if valid, 1 if invalid (or if fixed when --fix used)

set -euo pipefail

FEATURE_NAME="${1:-}"
FIX_MODE=false

if [[ "${2:-}" == "--fix" ]]; then
    FIX_MODE=true
fi

if [[ -z "$FEATURE_NAME" ]]; then
    echo "❌ Error: Feature name required"
    echo "Usage: $0 <feature-name> [--fix]"
    exit 1
fi

SESSION_FILE="specs/$FEATURE_NAME/session.md"

if [[ ! -f "$SESSION_FILE" ]]; then
    echo "❌ Error: Session file not found: $SESSION_FILE"
    exit 1
fi

# Extract session history entries (numbered or unnumbered)
# Look for lines like "1. **YYYY-MM-DD** - ..." OR "**YYYY-MM-DD** - ..." (old format)
extract_session_entries() {
    local file="$1"
    awk '
        /^### Session History \(Last 5\)/ { in_section=1; next }
        in_section && /^###/ && !/^### Session History/ { in_section=0 }
        in_section && /^[0-9]+\. \*\*[0-9]{4}-[0-9]{2}-[0-9]{2}\*\*/ { print; next }
        in_section && /^\*\*[0-9]{4}-[0-9]{2}-[0-9]{2}\*\*/ { print }
    ' "$file"
}

# Count session history entries
ENTRIES=$(extract_session_entries "$SESSION_FILE")
if [[ -z "$ENTRIES" ]]; then
    ENTRY_COUNT=0
else
    ENTRY_COUNT=$(echo "$ENTRIES" | wc -l | tr -d ' ')
fi

echo "📊 Session History Analysis for $FEATURE_NAME"
echo "   File: $SESSION_FILE"
echo "   Entries found: $ENTRY_COUNT"

if [[ $ENTRY_COUNT -le 5 ]]; then
    echo "✅ Session history valid ($ENTRY_COUNT/5 entries)"
    exit 0
fi

echo "❌ Session history has too many entries ($ENTRY_COUNT/5)"
echo ""
echo "Found entries:"
echo "$ENTRIES" | head -10 | nl -w2 -s'. '
echo ""

if [[ "$FIX_MODE" == false ]]; then
    echo "To fix automatically, run: $0 $FEATURE_NAME --fix"
    exit 1
fi

# Fix mode: Keep only first 5 entries, delete the rest
echo "🔧 Fixing session history (keeping first 5 entries)..."

# Create temp file with fixed history
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

# Process file: keep everything, but when in Session History section, limit to 5 entries
awk -v max_entries=5 '
    BEGIN { in_section=0; entry_count=0 }

    # Detect Session History section
    /^### Session History \(Last 5\)/ {
        in_section=1
        print
        next
    }

    # Exit section on next ### header
    in_section && /^###/ && !/^### Session History/ {
        in_section=0
        entry_count=0
    }

    # Handle numbered session history entries
    in_section && /^[0-9]+\. \*\*[0-9]{4}-[0-9]{2}-[0-9]{2}\*\*/ {
        entry_count++
        if (entry_count <= max_entries) {
            # Renumber entries sequentially (1, 2, 3, 4, 5)
            sub(/^[0-9]+\./, entry_count ".")
            print
        }
        next
    }

    # Handle unnumbered session history entries (old format) - convert to numbered
    in_section && /^\*\*[0-9]{4}-[0-9]{2}-[0-9]{2}\*\*/ {
        entry_count++
        if (entry_count <= max_entries) {
            # Add number prefix (1. 2. 3. 4. 5.)
            print entry_count ". " $0
        }
        next
    }

    # Pass through all other lines
    { print }
' "$SESSION_FILE" > "$TEMP_FILE"

# Backup original file
cp "$SESSION_FILE" "${SESSION_FILE}.backup"

# Replace with fixed version
mv "$TEMP_FILE" "$SESSION_FILE"

# Count entries in fixed file
FIXED_ENTRIES=$(extract_session_entries "$SESSION_FILE")
if [[ -z "$FIXED_ENTRIES" ]]; then
    FIXED_COUNT=0
else
    FIXED_COUNT=$(echo "$FIXED_ENTRIES" | wc -l | tr -d ' ')
fi

echo "✅ Session history fixed!"
echo "   Entries before: $ENTRY_COUNT"
echo "   Entries after: $FIXED_COUNT"
echo "   Backup saved: ${SESSION_FILE}.backup"
echo ""
echo "Fixed entries:"
echo "$FIXED_ENTRIES" | nl -w2 -s'. '

exit 0
