#!/bin/bash

# Context Monitoring Script for Advanced Context Engineering (ACE)
# Tracks context utilization and provides optimization recommendations
# Usage: context-monitor.sh [--check|--optimize|--report]

# --- Configuration ---
CONTEXT_TARGET_MIN=40
CONTEXT_TARGET_MAX=60
CONTEXT_WARNING_THRESHOLD=70
CONTEXT_CRITICAL_THRESHOLD=80

CONTEXT_LOG_FILE=".bifrost/context-usage.log"
CONTEXT_REPORT_FILE=".bifrost/context-report.md"

# --- Colors ---
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# --- Helper Functions ---

log_context_event() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local event_type="$1"
    local context_usage="$2"
    local details="$3"

    echo "$timestamp,$event_type,$context_usage,$details" >> "$CONTEXT_LOG_FILE"
}

estimate_context_usage() {
    # Simple estimation based on current session state
    # In practice, this would integrate with actual AI system metrics
    local total_chars=0
    local files_count=0

    # Count characters in key context files
    if [[ -f "RULES.md" ]]; then
        total_chars=$((total_chars + $(wc -c < "RULES.md")))
        files_count=$((files_count + 1))
    fi

    if [[ -d ".bifrost" ]]; then
        while IFS= read -r -d '' file; do
            if [[ "$file" == *.md ]]; then
                total_chars=$((total_chars + $(wc -c < "$file")))
                files_count=$((files_count + 1))
            fi
        done < <(find .bifrost -name "*.md" -print0)
    fi

    # Estimate context percentage (rough approximation)
    # Assuming ~200k character context window
    local context_percentage=$((total_chars * 100 / 200000))

    echo "$context_percentage"
}

check_context_health() {
    local context_usage=$(estimate_context_usage)
    local dashboard_mode="${1:-normal}"

    if [[ "$dashboard_mode" == "dashboard" ]]; then
        # Compact dashboard format for TUI
        local ts=$(date '+%H:%M:%S')
        echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${BLUE}║${NC} ${BOLD}Context Health Monitor${NC}                                    ${DIM}${ts}${NC} ${BLUE}║${NC}"
        echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
        echo

        # Visual gauge
        local bar_width=40
        local filled=$((context_usage * bar_width / 100))
        local empty=$((bar_width - filled))

        echo -ne "   ${BOLD}Context Usage:${NC} ["

        # Color-coded progress bar
        if [[ $context_usage -ge $CONTEXT_CRITICAL_THRESHOLD ]]; then
            echo -ne "${RED}"
        elif [[ $context_usage -ge $CONTEXT_WARNING_THRESHOLD ]]; then
            echo -ne "${YELLOW}"
        elif [[ $context_usage -ge $CONTEXT_TARGET_MIN ]]; then
            echo -ne "${GREEN}"
        else
            echo -ne "${BLUE}"
        fi

        printf "%${filled}s" | tr ' ' '█'
        echo -ne "${DIM}"
        printf "%${empty}s" | tr ' ' '░'
        echo -ne "${NC}] ${BOLD}${context_usage}%${NC}"

        # Trend indicator (placeholder - would need historical data)
        echo -e " ${DIM}→${NC}"
        echo

        # Status and quick action
        if [[ $context_usage -ge $CONTEXT_CRITICAL_THRESHOLD ]]; then
            echo -e "   ${RED}🚨 CRITICAL${NC} - Context critically high (>=${CONTEXT_CRITICAL_THRESHOLD}%)"
            echo -e "   ${BOLD}Action:${NC} Press 'o' to optimize | 'd' to delegate | 'r' to reset"
        elif [[ $context_usage -ge $CONTEXT_WARNING_THRESHOLD ]]; then
            echo -e "   ${YELLOW}⚠️  WARNING${NC} - Context high (>=${CONTEXT_WARNING_THRESHOLD}%)"
            echo -e "   ${BOLD}Suggested:${NC} Press 'o' to optimize | 'd' to delegate"
        elif [[ $context_usage -ge $CONTEXT_TARGET_MAX ]]; then
            echo -e "   ${YELLOW}📊 MODERATE${NC} - Above optimal range (target: ${CONTEXT_TARGET_MIN}-${CONTEXT_TARGET_MAX}%)"
            echo -e "   ${BOLD}Consider:${NC} Press 'o' to apply compaction"
        elif [[ $context_usage -ge $CONTEXT_TARGET_MIN ]]; then
            echo -e "   ${GREEN}✅ OPTIMAL${NC} - Within target range (${CONTEXT_TARGET_MIN}-${CONTEXT_TARGET_MAX}%)"
            echo -e "   ${DIM}Context utilization is healthy${NC}"
        else
            echo -e "   ${BLUE}📈 LOW${NC} - Below optimal range"
            echo -e "   ${DIM}Consider loading additional context if needed${NC}"
        fi

        echo
        echo -e "${BLUE}────────────────────────────────────────────────────────────────────────────${NC}"
        echo

        # Context breakdown
        echo -e "${BOLD}📊 Context Breakdown:${NC}"
        local rules_size=0
        local ai_files=0
        local specs_files=0

        [[ -f "RULES.md" ]] && rules_size=$(wc -c < "RULES.md" 2>/dev/null | tr -d ' ')
        [[ -d ".bifrost" ]] && ai_files=$(find .bifrost -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
        [[ -d "specs" ]] && specs_files=$(find specs -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

        echo -e "   Rules/Constitution: ${BLUE}~$((rules_size / 1000))k${NC} chars"
        echo -e "   Templates & Config: ${BLUE}${ai_files}${NC} files"
        echo -e "   Specs & Plans: ${BLUE}${specs_files}${NC} files"

        echo
        echo -e "${DIM}Monitoring active • Refresh every 30s${NC}"

    else
        # Original detailed format
        echo -e "${BLUE}=== Context Health Check ===${NC}"
        echo "Current estimated context usage: ${context_usage}%"
        echo "Target range: ${CONTEXT_TARGET_MIN}-${CONTEXT_TARGET_MAX}%"
        echo

        if [[ $context_usage -ge $CONTEXT_CRITICAL_THRESHOLD ]]; then
            echo -e "${RED}🚨 CRITICAL: Context usage is critically high (>=${CONTEXT_CRITICAL_THRESHOLD}%)${NC}"
            echo "Immediate action required:"
            echo "  1. Apply aggressive context compaction"
            echo "  2. Consider subagent delegation"
            echo "  3. Reset context with essential information only"
        elif [[ $context_usage -ge $CONTEXT_WARNING_THRESHOLD ]]; then
            echo -e "${YELLOW}⚠️  WARNING: Context usage is high (>=${CONTEXT_WARNING_THRESHOLD}%)${NC}"
            echo "Recommended actions:"
            echo "  1. Apply context optimization strategies"
            echo "  2. Consider subagent delegation for complex tasks"
            echo "  3. Compact non-essential information"
        elif [[ $context_usage -ge $CONTEXT_TARGET_MAX ]]; then
            echo -e "${YELLOW}📊 MODERATE: Context usage above optimal range${NC}"
            echo "Consider applying context compaction strategies"
        elif [[ $context_usage -ge $CONTEXT_TARGET_MIN ]]; then
            echo -e "${GREEN}✅ OPTIMAL: Context usage within target range${NC}"
            echo "Context utilization is healthy for effective AI interaction"
        else
            echo -e "${BLUE}📈 LOW: Context usage below optimal range${NC}"
            echo "Consider loading additional relevant context if needed"
        fi

        log_context_event "check" "$context_usage" "manual_check"
        echo
    fi
}

optimize_context() {
    echo -e "${BLUE}=== Context Optimization ===${NC}"

    local context_usage=$(estimate_context_usage)
    echo "Current context usage: ${context_usage}%"

    if [[ $context_usage -lt $CONTEXT_WARNING_THRESHOLD ]]; then
        echo -e "${GREEN}Context usage is acceptable. No optimization needed.${NC}"
        return 0
    fi

    echo "Applying context optimization strategies..."

    # Create optimization recommendations
    cat > .bifrost/context-optimization-recommendations.md << EOF
# Context Optimization Recommendations

**Current Usage**: ${context_usage}%
**Generated**: $(date)

## Immediate Actions

### High-Priority Compaction Opportunities
- [ ] Summarize project history into key insights only
- [ ] Compress detailed architecture docs into essential patterns
- [ ] Archive old feature specifications (keep summaries)
- [ ] Consolidate research findings into actionable conclusions

### Subagent Delegation Candidates
- [ ] Large codebase exploration tasks
- [ ] Comprehensive security analysis
- [ ] Cross-module pattern analysis
- [ ] Performance optimization research

### Context Reset Preparation
If optimization is insufficient, prepare for context reset:
- [ ] Save essential project constitution and principles
- [ ] Preserve current feature specifications and requirements
- [ ] Maintain critical architectural decisions and constraints
- [ ] Keep active task context and integration requirements

## Optimization Commands

\`\`\`bash
# Apply recommended optimizations
.bifrost/scripts/context-monitor.sh --apply-optimizations

# Delegate tasks to subagents
claude /subagent-delegate [task-type] [scope]

# Emergency context reset (if needed)
.bifrost/scripts/context-monitor.sh --emergency-reset
\`\`\`
EOF

    echo -e "${GREEN}✅ Optimization recommendations generated: .bifrost/context-optimization-recommendations.md${NC}"
    log_context_event "optimize" "$context_usage" "recommendations_generated"
}

generate_context_report() {
    echo -e "${BLUE}=== Generating Context Usage Report ===${NC}"

    local current_usage=$(estimate_context_usage)

    cat > "$CONTEXT_REPORT_FILE" << EOF
# Context Usage Report

**Generated**: $(date)
**Current Usage**: ${current_usage}%

## Usage Analysis

### Current Status
- **Context Utilization**: ${current_usage}%
- **Health Status**: $(if [[ $current_usage -ge $CONTEXT_CRITICAL_THRESHOLD ]]; then echo "CRITICAL"; elif [[ $current_usage -ge $CONTEXT_WARNING_THRESHOLD ]]; then echo "WARNING"; elif [[ $current_usage -ge $CONTEXT_TARGET_MAX ]]; then echo "MODERATE"; elif [[ $current_usage -ge $CONTEXT_TARGET_MIN ]]; then echo "OPTIMAL"; else echo "LOW"; fi)
- **Optimization Needed**: $(if [[ $current_usage -ge $CONTEXT_WARNING_THRESHOLD ]]; then echo "Yes"; else echo "No"; fi)

### Context Composition Estimate
EOF

    if [[ -f "RULES.md" ]]; then
        local rules_size=$(wc -c < "RULES.md")
        echo "- **Project Constitution**: ~$((rules_size / 1000))k characters" >> "$CONTEXT_REPORT_FILE"
    fi

    if [[ -d ".bifrost" ]]; then
        local ai_files=$(find .bifrost -name "*.md" | wc -l)
        echo "- **AI Templates & Config**: ~${ai_files} files" >> "$CONTEXT_REPORT_FILE"
    fi

    cat >> "$CONTEXT_REPORT_FILE" << EOF

## Recent Context Events
EOF

    if [[ -f "$CONTEXT_LOG_FILE" ]]; then
        echo "| Timestamp | Event | Usage | Details |" >> "$CONTEXT_REPORT_FILE"
        echo "|-----------|-------|-------|---------|" >> "$CONTEXT_REPORT_FILE"
        tail -10 "$CONTEXT_LOG_FILE" | while IFS=, read -r timestamp event usage details; do
            echo "| $timestamp | $event | $usage% | $details |" >> "$CONTEXT_REPORT_FILE"
        done
    else
        echo "No context events logged yet." >> "$CONTEXT_REPORT_FILE"
    fi

    cat >> "$CONTEXT_REPORT_FILE" << EOF

## Recommendations

### For Current Usage Level (${current_usage}%)
EOF

    if [[ $current_usage -ge $CONTEXT_CRITICAL_THRESHOLD ]]; then
        cat >> "$CONTEXT_REPORT_FILE" << EOF
🚨 **CRITICAL ACTIONS REQUIRED**
1. Immediately apply aggressive context compaction
2. Delegate complex tasks to subagents
3. Consider emergency context reset with essential information only
4. Pause non-critical activities until context is optimized
EOF
    elif [[ $current_usage -ge $CONTEXT_WARNING_THRESHOLD ]]; then
        cat >> "$CONTEXT_REPORT_FILE" << EOF
⚠️ **OPTIMIZATION RECOMMENDED**
1. Apply context compaction strategies
2. Consider subagent delegation for research/implementation tasks
3. Summarize non-essential historical information
4. Monitor context usage more frequently
EOF
    elif [[ $current_usage -ge $CONTEXT_TARGET_MAX ]]; then
        cat >> "$CONTEXT_REPORT_FILE" << EOF
📊 **MINOR OPTIMIZATION BENEFICIAL**
1. Review and compact older context elements
2. Consider selective information summarization
3. Maintain current monitoring frequency
EOF
    else
        cat >> "$CONTEXT_REPORT_FILE" << EOF
✅ **CONTEXT HEALTHY**
1. Continue current context management practices
2. Monitor during complex feature development
3. Proactively apply ACE principles for new features
EOF
    fi

    echo -e "${GREEN}✅ Context report generated: $CONTEXT_REPORT_FILE${NC}"
    log_context_event "report" "$current_usage" "report_generated"
}

apply_optimizations() {
    echo -e "${BLUE}=== Applying Context Optimizations ===${NC}"

    # Create backup of current context state
    local backup_dir=".bifrost/context-backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"

    if [[ -d ".bifrost" ]]; then
        cp -r .bifrost/* "$backup_dir/" 2>/dev/null || true
    fi

    echo "✅ Context backup created: $backup_dir"

    # Apply optimizations (placeholder for actual optimization logic)
    echo "🔧 Applying context optimizations..."

    # Archive old specifications
    if [[ -d "specs" ]]; then
        mkdir -p ".bifrost/archived-specs"
        find specs -name "*.md" -mtime +30 -exec mv {} .bifrost/archived-specs/ \; 2>/dev/null || true
    fi

    # Compress research files
    if [[ -d ".bifrost" ]]; then
        find .bifrost -name "research*.md" -exec gzip {} \; 2>/dev/null || true
    fi

    local new_usage=$(estimate_context_usage)
    echo -e "${GREEN}✅ Optimizations applied. New usage estimate: ${new_usage}%${NC}"
    log_context_event "optimize_applied" "$new_usage" "automatic_optimization"
}

emergency_reset() {
    echo -e "${RED}=== EMERGENCY CONTEXT RESET ===${NC}"
    echo -e "${YELLOW}This will reset context to essential information only.${NC}"
    read -p "Are you sure? (yes/no): " confirmation

    if [[ "$confirmation" != "yes" ]]; then
        echo "Reset cancelled."
        return 1
    fi

    # Create emergency backup
    local emergency_backup=".bifrost/emergency-backup-$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$emergency_backup"
    cp -r .bifrost/* "$emergency_backup/" 2>/dev/null || true
    cp RULES.md "$emergency_backup/" 2>/dev/null || true

    echo "🔒 Emergency backup created: $emergency_backup"

    # Reset to essential context only
    mkdir -p .bifrost/essential

    # Preserve only essential files
    if [[ -f "RULES.md" ]]; then
        cp RULES.md .bifrost/essential/
    fi

    if [[ -f ".bifrost/commands/context-manager-template.md" ]]; then
        cp .bifrost/commands/context-manager-template.md .bifrost/essential/
    fi

    echo -e "${GREEN}✅ Emergency context reset completed.${NC}"
    echo "Essential information preserved in .bifrost/essential/"
    echo "Full backup available in: $emergency_backup"

    log_context_event "emergency_reset" "10" "context_reset_to_essentials"
}

show_usage() {
    echo "Context Monitor - Advanced Context Engineering (ACE) Tool"
    echo
    echo "Usage: $0 [OPTION]"
    echo
    echo "Options:"
    echo "  --check, -c              Check current context health"
    echo "  --optimize, -o           Generate optimization recommendations"
    echo "  --report, -r             Generate detailed context usage report"
    echo "  --apply-optimizations    Apply automatic context optimizations"
    echo "  --emergency-reset        Emergency context reset (interactive)"
    echo "  --help, -h               Show this help message"
    echo
    echo "Examples:"
    echo "  $0 --check              # Quick context health check"
    echo "  $0 --report             # Detailed usage analysis"
    echo "  $0 --optimize           # Get optimization recommendations"
}

# --- Main Logic ---

# Create necessary directories
mkdir -p .bifrost/context-backups

# Initialize log file if it doesn't exist
if [[ ! -f "$CONTEXT_LOG_FILE" ]]; then
    echo "timestamp,event_type,context_usage,details" > "$CONTEXT_LOG_FILE"
fi

# Parse command line arguments
case "${1:-}" in
    --check|-c)
        check_context_health
        ;;
    --dashboard|-d)
        check_context_health "dashboard"
        ;;
    --optimize|-o)
        optimize_context
        ;;
    --report|-r)
        generate_context_report
        ;;
    --apply-optimizations)
        apply_optimizations
        ;;
    --emergency-reset)
        emergency_reset
        ;;
    --help|-h)
        show_usage
        ;;
    "")
        check_context_health
        ;;
    *)
        echo "Unknown option: $1"
        show_usage
        exit 1
        ;;
esac