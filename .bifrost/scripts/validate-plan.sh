#!/bin/bash

# Validates a plan file for completeness and constitution compliance
# Usage: validate-plan.sh <plan-file-path> [constitution-file-path]

PLAN_FILE="$1"
CONSTITUTION_FILE="${2:-RULES.md}"

if [[ -z "$PLAN_FILE" || ! -f "$PLAN_FILE" ]]; then
    echo "❌ Error: Plan file not found or not provided"
    echo "Usage: validate-plan.sh <plan-file-path> [constitution-file-path]"
    exit 1
fi

echo "🔍 Validating plan: $PLAN_FILE"
echo

# Check for required sections
REQUIRED_SECTIONS=("Technical Context" "Constitution Check" "Phase 0: ACE-Enhanced Research & Exploration" "Phase 1: Design & Contracts")
MISSING_SECTIONS=()

for section in "${REQUIRED_SECTIONS[@]}"; do
    if ! grep -q "## $section" "$PLAN_FILE"; then
        MISSING_SECTIONS+=("$section")
    fi
done

# Check for unresolved clarifications
CLARIFICATION_COUNT=$(grep -c "\[NEEDS CLARIFICATION\]" "$PLAN_FILE" 2>/dev/null || echo 0)
CLARIFICATION_COUNT=$(echo "$CLARIFICATION_COUNT" | tr -d '\n\r' | head -n1)

# Check constitution compliance
CONSTITUTION_RULES=0
CONSTITUTION_EVIDENCE=0

if [[ -f "$CONSTITUTION_FILE" ]]; then
    # Count rules in constitution (assumes ## numbered sections)
    CONSTITUTION_RULES=$(grep -c "^##" "$CONSTITUTION_FILE" 2>/dev/null || echo 0)
    CONSTITUTION_RULES=$(echo "$CONSTITUTION_RULES" | tr -d '\n\r' | head -n1)

    # Count evidence entries in plan
    CONSTITUTION_EVIDENCE=$(grep -c "\*\*Rule [0-9]\+" "$PLAN_FILE" 2>/dev/null || echo 0)
    CONSTITUTION_EVIDENCE=$(echo "$CONSTITUTION_EVIDENCE" | tr -d '\n\r' | head -n1)
fi

# Check for design artifacts mentioned
DESIGN_ARTIFACTS=("data-model.md" "contracts" "failing test")
MISSING_ARTIFACTS=()

for artifact in "${DESIGN_ARTIFACTS[@]}"; do
    if ! grep -qi "$artifact" "$PLAN_FILE"; then
        MISSING_ARTIFACTS+=("$artifact")
    fi
done

# Check for complexity tracking
COMPLEXITY_TABLE=$(grep -c "| Violation | Justification |" "$PLAN_FILE" 2>/dev/null || echo 0)
COMPLEXITY_TABLE=$(echo "$COMPLEXITY_TABLE" | tr -d '\n\r' | head -n1)

# Report results
echo "📊 Validation Results:"
echo "====================="

if [[ ${#MISSING_SECTIONS[@]} -eq 0 ]]; then
    echo "✅ All required sections present"
else
    echo "❌ Missing sections: ${MISSING_SECTIONS[*]}"
fi

if [[ $CLARIFICATION_COUNT -eq 0 ]]; then
    echo "✅ No unresolved clarifications"
else
    echo "❌ $CLARIFICATION_COUNT unresolved clarifications found"
fi

if [[ $CONSTITUTION_EVIDENCE -gt 0 ]]; then
    echo "✅ Constitution compliance documented ($CONSTITUTION_EVIDENCE rules addressed)"
else
    echo "⚠️  No constitution compliance evidence found"
fi

if [[ ${#MISSING_ARTIFACTS[@]} -eq 0 ]]; then
    echo "✅ All design artifacts referenced"
else
    echo "⚠️  Missing artifact references: ${MISSING_ARTIFACTS[*]}"
fi

if [[ $COMPLEXITY_TABLE -gt 0 ]]; then
    echo "✅ Complexity tracking table present"
else
    echo "⚠️  No complexity tracking table found"
fi

# Overall validation
CRITICAL_FAILURES=$((${#MISSING_SECTIONS[@]} + $CLARIFICATION_COUNT))

if [[ $CRITICAL_FAILURES -eq 0 ]]; then
    echo
    echo "🎉 Plan validation PASSED"
    exit 0
else
    echo
    echo "🚫 Plan validation FAILED ($CRITICAL_FAILURES critical issues)"
    exit 1
fi
