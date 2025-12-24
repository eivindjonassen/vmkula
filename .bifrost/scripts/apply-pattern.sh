#!/bin/bash

# Applies a discovered pattern to the current project
# Usage: apply-pattern.sh <pattern-name> [target-directory]

PATTERN_NAME="$1"
TARGET_DIR="${2:-.}"
PATTERNS_DIR=".bifrost/patterns"
PATTERN_FILE="$PATTERNS_DIR/$PATTERN_NAME.md"

if [[ -z "$PATTERN_NAME" ]]; then
    echo "❌ Error: Pattern name required"
    echo "Usage: apply-pattern.sh <pattern-name> [target-directory]"
    echo
    echo "Available patterns:"
    if [[ -d "$PATTERNS_DIR" ]]; then
        ls "$PATTERNS_DIR"/*.md 2>/dev/null | sed 's|.*/||; s|\.md$||' | sed 's/^/  - /'
    else
        echo "  No patterns found. Run /discover-patterns first."
    fi
    exit 1
fi

if [[ ! -f "$PATTERN_FILE" ]]; then
    echo "❌ Error: Pattern '$PATTERN_NAME' not found"
    echo "Available patterns:"
    ls "$PATTERNS_DIR"/*.md 2>/dev/null | sed 's|.*/||; s|\.md$||' | sed 's/^/  - /' || echo "  No patterns found"
    exit 1
fi

echo "🎨 Applying pattern: $PATTERN_NAME"
echo "📁 Target directory: $TARGET_DIR"
echo

# Extract pattern information
CATEGORY=$(grep "^**Category**:" "$PATTERN_FILE" | sed 's/.*: \[//' | sed 's/\].*//')
COMPLEXITY=$(grep "^**Complexity**:" "$PATTERN_FILE" | sed 's/.*: \[//' | sed 's/\].*//')

echo "📊 Pattern Info:"
echo "   Category: $CATEGORY"
echo "   Complexity: $COMPLEXITY"
echo

# Check prerequisites
echo "🔍 Checking prerequisites..."

# Extract dependencies from pattern file
if grep -q "### Dependencies" "$PATTERN_FILE"; then
    echo "📦 Dependencies found in pattern. Please review:"
    sed -n '/### Dependencies/,/^### /p' "$PATTERN_FILE" | head -n -1
    echo
fi

# Check if target directory exists
if [[ ! -d "$TARGET_DIR" ]]; then
    echo "📁 Creating target directory: $TARGET_DIR"
    mkdir -p "$TARGET_DIR"
fi

# Interactive confirmation
echo "❓ This will apply the pattern to $TARGET_DIR"
echo "   Please review the pattern file first: $PATTERN_FILE"
echo
read -p "Continue? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Pattern application cancelled"
    exit 0
fi

# Apply pattern (this would be enhanced based on specific pattern structure)
echo "🔧 Applying pattern..."

# Extract file generation instructions
if grep -q "### File Generation" "$PATTERN_FILE"; then
    echo "📝 Files to generate found in pattern"
    echo "   Please manually create files as described in:"
    echo "   $PATTERN_FILE (File Generation section)"
    echo
fi

# Extract modification instructions
if grep -q "### Existing File Modifications" "$PATTERN_FILE"; then
    echo "✏️  File modifications found in pattern"
    echo "   Please review and apply changes described in:"
    echo "   $PATTERN_FILE (Existing File Modifications section)"
    echo
fi

# Log pattern application
PATTERN_LOG=".bifrost/pattern-applications.log"
echo "$(date): Applied pattern '$PATTERN_NAME' to '$TARGET_DIR'" >> "$PATTERN_LOG"

echo "✅ Pattern application guidance provided"
echo "📋 Review the pattern file for detailed implementation steps:"
echo "   $PATTERN_FILE"
echo
echo "📄 Application logged to: $PATTERN_LOG"

# Suggest next steps
echo "💡 Next steps:"
echo "   1. Review pattern documentation"
echo "   2. Create/modify files as described"
echo "   3. Test the implementation"
echo "   4. Document any customizations made"