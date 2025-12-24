#!/bin/bash

# Log Compliance/Log Tail Monitor (interactive)
# Default: clean tail of agent log. Toggle to compliance summary mode with 'c'.

set -euo pipefail

PROJECT_ROOT="${BIFROST_PROJECT_ROOT:-$(pwd)}"
LOGS_DIR="$PROJECT_ROOT/.bifrost/logs"
LOG_FILE="$LOGS_DIR/agent-current.log"

mkdir -p "$LOGS_DIR"
touch "$LOG_FILE"

MODE="intelligence"   # intelligence | tail | scan
TAIL_PID=""

SCRIPTS_DIR="$PROJECT_ROOT/.bifrost/scripts"

cleanup() {
  if [[ -n "$TAIL_PID" ]] && kill -0 "$TAIL_PID" 2>/dev/null; then
    kill "$TAIL_PID" 2>/dev/null || true
    wait "$TAIL_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

header() {
  echo "[Compliance] Mode: $(echo "$MODE" | tr '[:lower:]' '[:upper:]')  |  Keys: t=tail, s=scan, i=intelligence, r=refresh, q=quit  |  $(date '+%H:%M:%S')"
  echo "--------------------------------------------------------------------------------"
}

start_tail() {
  cleanup
  clear
  header
  # Show last 200 lines and follow, strip ANSI sequences and carriage returns, hide script header lines
  (
    tail -n 200 -F "$LOG_FILE" 2>/dev/null \
    | sed -u -e 's/\x1b\[[0-9;]*[A-Za-z]//g' -e 's/\r//g' \
    | grep -vE '^(Script (started|done) on|The default interactive shell is now zsh\.|bash: -c: line 0:)' \
    | grep -vE '^select an agent to run:'
  ) &
  TAIL_PID=$!
}

scan_once() {
  clear
  header
  local last_1000
  last_1000=$(tail -n 1000 "$LOG_FILE" 2>/dev/null || true)

  # Gates and signals (compact)
  echo "Gates:"
  echo "$last_1000" | grep -E "PLANNING COMPLETE|MANDATORY STOP|Plan validation PASSED|Specification validation PASSED" -n | tail -n 5 || echo "  (none)"

  # Potential issues (compact)
  echo
  echo "Potential issues:"
  echo "$last_1000" | grep -E "❌|ERROR|FAILED|violation|Constitution violations|validation FAILED" -n | tail -n 10 || echo "  (none)"

  # Recent commands (heuristic)
  echo
  echo "Recent commands:"
  echo "$last_1000" | grep -E "^/spec |^/plan |^/tasks |^/implement |/polish" -n | tail -n 5 || echo "  (none)"

  # If no gates/commands detected, show a short recent output preview for context
  if ! echo "$last_1000" | grep -Eq "PLANNING COMPLETE|MANDATORY STOP|Plan validation PASSED|Specification validation PASSED|^/spec |^/plan |^/tasks |^/implement |/polish"; then
    echo
    echo "Recent output (last 20 lines):"
    tail -n 20 "$LOG_FILE" 2>/dev/null | sed -u -e 's/\x1b\[[0-9;]*[A-Za-z]//g' -e 's/\r//g'
  fi
}

show_intelligence() {
  clear
  if [[ -x "$SCRIPTS_DIR/bifrost-log-intelligence.sh" ]]; then
    "$SCRIPTS_DIR/bifrost-log-intelligence.sh" --dashboard
  else
    header
    echo "Intelligence module not available"
    echo "Install bifrost-log-intelligence.sh to enable smart analysis"
  fi
}

main_loop() {
  # Start in intelligence mode by default
  show_intelligence

  while true; do
    if read -rsn1 -t 1 key; then
      case "$key" in
        t|T)
          MODE="tail"; cleanup; start_tail
          ;;
        s|S)
          MODE="scan"; cleanup; scan_once
          ;;
        i|I)
          MODE="intelligence"; cleanup; show_intelligence
          ;;
        r|R)
          if [[ "$MODE" == "scan" ]]; then
            scan_once
          elif [[ "$MODE" == "intelligence" ]]; then
            show_intelligence
          else
            start_tail
          fi
          ;;
        q|Q)
          echo "Exiting compliance monitor..."; exit 0 ;;
      esac
    fi
    if [[ "$MODE" == "scan" ]] || [[ "$MODE" == "intelligence" ]]; then
      sleep 5
    fi
  done
}

main_loop
