#!/bin/bash

# Command compliance wrapper
# Decides which validator to run based on file path or runs all if none provided

set -euo pipefail

PROJECT_ROOT="${BIFROST_PROJECT_ROOT:-$(pwd)}"
SCRIPTS_DIR="$PROJECT_ROOT/.bifrost/scripts"

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

QUIET="${BIFROST_QUIET:-0}"

validate_file() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo -e "${YELLOW}⚠️  Skipping missing file:${NC} $file"
    return 0
  fi
  if [[ "$file" == *"/spec.md" ]]; then
    if [[ "$QUIET" == "1" ]]; then
      "$SCRIPTS_DIR/validate-spec.sh" "$file" >/dev/null 2>&1
      return $?
    else
      echo -e "\n🔎 Validating spec: $file"
      if "$SCRIPTS_DIR/validate-spec.sh" "$file"; then
        echo -e "${GREEN}✅ SPEC PASS${NC}"
        return 0
      else
        echo -e "${RED}❌ SPEC FAIL${NC}"
        return 1
      fi
    fi
  elif [[ "$file" == *"/plan.md" ]]; then
    if [[ "$QUIET" == "1" ]]; then
      "$SCRIPTS_DIR/validate-plan.sh" "$file" >/dev/null 2>&1
      return $?
    else
      echo -e "\n🔎 Validating plan: $file"
      if "$SCRIPTS_DIR/validate-plan.sh" "$file"; then
        echo -e "${GREEN}✅ PLAN PASS${NC}"
        return 0
      else
        echo -e "${RED}❌ PLAN FAIL${NC}"
        return 1
      fi
    fi
  else
    echo -e "${YELLOW}ℹ️  Unknown file type, skipping:${NC} $file"
    return 0
  fi
}

quiet_summary() {
  local files=("$@")
  local spec_total=0 plan_total=0
  local spec_fail=0 plan_fail=0
  local spec_failed_files=() plan_failed_files=()

  # If no files provided, scan defaults
  if [[ ${#files[@]} -eq 0 ]]; then
    while IFS= read -r f; do files+=("$f"); done < <(find specs -type f -name 'spec.md' 2>/dev/null || true)
    while IFS= read -r f; do files+=("$f"); done < <(find specs -type f -name 'plan.md' 2>/dev/null || true)
  fi

  # Check if files array is empty after population
  if [[ ${#files[@]} -eq 0 ]]; then
    local ts
    ts=$(date '+%H:%M:%S')
    echo -e "${GREEN}✔ No specs/plans found${NC} at ${ts}"
    return 0
  fi

  for f in "${files[@]}"; do
    [[ ! -f "$f" ]] && continue
    if [[ "$f" == *"/spec.md" ]]; then
      spec_total=$((spec_total+1))
      if ! "$SCRIPTS_DIR/validate-spec.sh" "$f" >/dev/null 2>&1; then
        spec_fail=$((spec_fail+1))
        spec_failed_files+=("$f")
      fi
    elif [[ "$f" == *"/plan.md" ]]; then
      plan_total=$((plan_total+1))
      if ! "$SCRIPTS_DIR/validate-plan.sh" "$f" >/dev/null 2>&1; then
        plan_fail=$((plan_fail+1))
        plan_failed_files+=("$f")
      fi
    fi
  done

  local ts
  ts=$(date '+%H:%M:%S')
  if [[ $spec_fail -eq 0 && $plan_fail -eq 0 ]]; then
    echo -e "${GREEN}✔ All validations passed${NC} at ${ts}  (specs: ${spec_total}, plans: ${plan_total})"
    return 0
  fi

  echo -e "${RED}✖ Validation failures at ${ts}${NC}"
  if [[ $spec_fail -gt 0 ]]; then
    echo "- Specs failed: ${spec_fail}/${spec_total}"
    for f in "${spec_failed_files[@]}"; do echo "  • $f"; done | sed -n '1,6p'
    [[ $spec_fail -gt 6 ]] && echo "  … and more"
  fi
  if [[ $plan_fail -gt 0 ]]; then
    echo "- Plans failed: ${plan_fail}/${plan_total}"
    for f in "${plan_failed_files[@]}"; do echo "  • $f"; done | sed -n '1,6p'
    [[ $plan_fail -gt 6 ]] && echo "  … and more"
  fi
  echo "(Run .bifrost/scripts/command-compliance.sh <file> for details)"
  return 1
}

if [[ "$QUIET" == "1" ]]; then
  quiet_summary "$@"
  exit $?
fi

if [[ $# -gt 0 ]]; then
  rc=0
  for f in "$@"; do
    validate_file "$f" || rc=1
  done
  exit $rc
fi

# No args: verbose validate all known files
rc=0
while IFS= read -r f; do
  validate_file "$f" || rc=1
done < <(find specs -type f -name 'spec.md' 2>/dev/null || true)
while IFS= read -r f; do
  validate_file "$f" || rc=1
done < <(find specs -type f -name 'plan.md' 2>/dev/null || true)
exit $rc
