#!/bin/bash

# Validates a specification file for completeness and quality
# Usage: validate-spec.sh <spec-file-path>

SPEC_FILE="$1"

if [[ -z "$SPEC_FILE" || ! -f "$SPEC_FILE" ]]; then
    echo "❌ Error: Specification file not found or not provided"
    echo "Usage: validate-spec.sh <spec-file-path>"
    exit 1
fi

echo "🔍 Validating specification: $SPEC_FILE"
echo

# Check for required sections
REQUIRED_SECTIONS=("User Scenarios & Testing" "Requirements" "Review & Acceptance Checklist")
MISSING_SECTIONS=()

for section in "${REQUIRED_SECTIONS[@]}"; do
    if ! grep -q "## $section" "$SPEC_FILE"; then
        MISSING_SECTIONS+=("$section")
    fi
done

# Check for clarification markers
CLARIFICATION_COUNT=$(grep -c "\[NEEDS CLARIFICATION:" "$SPEC_FILE" 2>/dev/null || echo 0)
CLARIFICATION_COUNT=$(echo "$CLARIFICATION_COUNT" | tr -d '\n\r' | head -n1)

# Extract content before the checklist section to avoid false positives
# The checklist itself mentions implementation keywords as examples
CONTENT_TO_VALIDATE=$(awk '/^## Review & Acceptance Checklist/{exit} {print}' "$SPEC_FILE")

# Check for implementation details (anti-patterns)
IMPLEMENTATION_KEYWORDS=("database" "API endpoint" "React" "Node.js" "PostgreSQL" "MongoDB" "framework" "library")
IMPLEMENTATION_ISSUES=()

for keyword in "${IMPLEMENTATION_KEYWORDS[@]}"; do
    if echo "$CONTENT_TO_VALIDATE" | grep -qi "$keyword"; then
        IMPLEMENTATION_ISSUES+=("$keyword")
    fi
done

# Check for testable requirements
FR_COUNT=$(grep -c "^- \*\*FR-[0-9]\+\*\*:" "$SPEC_FILE" 2>/dev/null || echo 0)
FR_COUNT=$(echo "$FR_COUNT" | tr -d '\n\r' | head -n1)

# Report results
echo "📊 Validation Results:"
echo "====================="

if [[ ${#MISSING_SECTIONS[@]} -eq 0 ]]; then
    echo "✅ All required sections present"
else
    echo "❌ Missing sections: ${MISSING_SECTIONS[*]}"
fi

if [[ $CLARIFICATION_COUNT -eq 0 ]]; then
    echo "✅ No clarification markers remaining"
else
    echo "⚠️  $CLARIFICATION_COUNT clarification markers found"
fi

if [[ ${#IMPLEMENTATION_ISSUES[@]} -eq 0 ]]; then
    echo "✅ No implementation details detected"
else
    echo "❌ Implementation details found: ${IMPLEMENTATION_ISSUES[*]}"
fi

if [[ $FR_COUNT -gt 0 ]]; then
    echo "✅ $FR_COUNT functional requirements defined"
else
    echo "❌ No functional requirements found"
fi

# Overall validation
if [[ ${#MISSING_SECTIONS[@]} -eq 0 && $CLARIFICATION_COUNT -eq 0 && ${#IMPLEMENTATION_ISSUES[@]} -eq 0 && $FR_COUNT -gt 0 ]]; then
    echo
    echo "🎉 Specification validation PASSED"
    exit 0
else
    echo
    echo "🚫 Specification validation FAILED"
    exit 1
fi