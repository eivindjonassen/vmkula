---
description: Resume interrupted or paused workflow from last checkpoint
---

# Resume Workflow: $ARGUMENTS

**User Input**: `/resume $ARGUMENTS` (or `/resume` for auto-detect)
**Purpose**: Resume interrupted or paused workflow from last checkpoint

## Execution Flow

1. **Detect Feature to Resume**:
   - If feature name provided: Use it directly (e.g., `/resume user-authentication`)
   - If no feature name: Attempt auto-detection:
     - Check `.bifrost/active-workflow` for current feature
     - If found: Use that feature
     - If not found or empty: List available features from `specs/*/` and ask user to select

2. **Load Session Memory**:
   - **Feature-Specific Session Path**: Try feature-specific session first, fall back to legacy format for backward compatibility
   - **Try new format first**: Read `specs/[feature-name]/session.md` if feature name available
   - **Backward Compatibility Check**: If new format doesn't exist, check legacy format: `.bifrost/memory/session.md`
     ```bash
     # Load session with feature-specific preference
     FEATURE_SESSION="specs/[feature-name]/session.md"
     LEGACY_SESSION=".bifrost/memory/session.md"

     if [[ -f "$FEATURE_SESSION" ]]; then
       SESSION_FILE="$FEATURE_SESSION"
     elif [[ -f "$LEGACY_SESSION" ]]; then
       SESSION_FILE="$LEGACY_SESSION"
       echo "⚠️  Using legacy session format. Consider migrating: .bifrost/scripts/migrate-session-memory.sh [feature-name]"
     else
       echo "❌ ERROR: No session memory found (tried $FEATURE_SESSION and $LEGACY_SESSION). Cannot resume without previous session context. Start new feature with \`/spec\`."
       exit 1
     fi
     ```
   - Read the selected session file to get full context
   - Extract Latest Checkpoint section for resume information

3. **Validate Latest Checkpoint**:
   - Verify checkpoint exists in session memory
   - Extract checkpoint metadata:
     - Checkpoint ID and timestamp
     - Phase (spec/plan/tasks/implement)
     - Status (Complete/In Progress)
     - Context utilization percentage
     - Artifacts list (files that should exist)
     - Dependencies (what prerequisites are satisfied)
     - Next action (exact command to continue)
   - If no checkpoint found: Stop with error "❌ ERROR: No valid checkpoint found in session memory. Start workflow with `/spec [feature-name]`."

4. **Verify Checkpoint Integrity**:
   - **Artifact Validation**:
     - Check that all artifacts listed in checkpoint actually exist
     - For each missing artifact, add to issues list
     - If critical artifacts missing (spec.md, plan.md, tasks.md depending on phase): Report as blocker
   - **Dependency Validation**:
     - Verify dependencies mentioned in checkpoint are satisfied
     - Check file timestamps to detect if artifacts were modified after checkpoint
     - If modifications detected: Warn user about potential stale checkpoint
   - **Workflow Marker Consistency**:
     - Read `.bifrost/active-workflow` if exists
     - Compare with checkpoint phase
     - If mismatch: Use checkpoint as source of truth, update marker
   - **Phase Completeness**:
     - Verify completed phases match checkpoint status
     - Check validation status for completed phases

5. **Context Reconstruction**:
   - Load context from session memory sections:
     - **Active Focus**: Feature, phase, status, task info
     - **Session History**: Last session's accomplishments
     - **Key Decisions**: Architectural and design choices
     - **Context Carryover**: Information from spec → plan → tasks
     - **Known Issues & Blockers**: Active blockers (if any)
     - **Progress Tracking**: Phase completion status
   - Estimate current context utilization based on loaded information
   - If context appears high (>60%), flag for potential optimization

6. **Resume Summary Generation**:
   - Create comprehensive summary showing:
     - **Last Session**: When work was last done (checkpoint timestamp)
     - **Accomplished**: What was completed (from checkpoint and session history)
     - **Current State**: What phase/status we're resuming at
     - **Context Available**: What information has been preserved
     - **Next Step**: Clear action to take (from checkpoint)
   - Include any warnings or issues found during validation

7. **Present Resume Plan to User**:
   - Display resume summary with clear structure
   - Show checkpoint details (timestamp, phase, artifacts)
   - List what will happen when resuming
   - Show next recommended command
   - Ask for confirmation: "Ready to resume from this checkpoint? (y/n/details)"
     - If "details": Show full checkpoint metadata and artifact list
     - If "n": Exit without changing state
     - If "y": Proceed to step 8

8. **Update Workflow State for Resume**:
   - Update `.bifrost/active-workflow` marker:
     - Set feature name
     - Set active phase from checkpoint
     - Preserve completed phases from checkpoint
     - Format: `specs/[feature-name]:[active-phase]|[completed-phases]`
   - Update session memory Active Focus:
     - Set status to "Resuming" initially
     - Preserve feature, phase, and task info from checkpoint
     - Add resume note to Session History
   - Verify state is consistent and resumable

9. **Provide Resumption Guidance**:
   - Show user exactly what to do next
   - Display full command to continue (from checkpoint's "Next" field)
   - Explain current context and what's been accomplished
   - Offer relevant tips based on phase:
     - **Spec phase**: Remind about validation and clarifications
     - **Plan phase**: Note context optimization strategies if context high
     - **Tasks phase**: Show task breakdown structure
     - **Implement phase**: Show current task progress and next task

10. **Log Resume Action**:
    - Add resume entry to session history:
      - Format: `**YYYY-MM-DD** - Resume: Resumed [feature-name] at [phase] phase from checkpoint CP-XXX ([timestamp]). [Brief context note].`
    - Update "Last Updated" timestamp in session memory

11. **✋ MANDATORY STOP**: End here with resume complete message:
    ```
    ✅ **WORKFLOW RESUMED** from checkpoint CP-XXX

    Last checkpoint: [timestamp]
    Resuming phase: [phase-name]
    Next action: [exact command]

    Context preserved: [X%] utilization
    Artifacts verified: [X/Y present]

    Run the command above to continue your workflow.
    ```

---

## Resume Validation Checklist

Before allowing resume, verify:

- [ ] **Session Memory Exists**: `.bifrost/memory/session.md` is present and readable
- [ ] **Valid Checkpoint**: Latest checkpoint section has all required metadata
- [ ] **Artifacts Present**: All critical artifacts from checkpoint exist
- [ ] **Dependencies Met**: Prerequisites listed in checkpoint are satisfied
- [ ] **Workflow Coherence**: Active workflow marker consistent with checkpoint
- [ ] **No Corruption**: Session memory is valid markdown and parseable
- [ ] **Reasonable Timestamp**: Checkpoint is not suspiciously old (>30 days - warn user)

---

## Checkpoint Compatibility Matrix

Different phases have different resumability requirements:

### Spec Phase Resume
- **Required Artifacts**: `specs/[feature]/spec.md`
- **Dependencies**: None (can always resume spec)
- **Next Action**: Continue spec refinement or proceed to `/plan`
- **Context**: Lightweight, easy to restore

### Plan Phase Resume
- **Required Artifacts**: `specs/[feature]/spec.md`, `specs/[feature]/plan.md` (may be partial)
- **Dependencies**: Valid spec.md (validated)
- **Next Action**: Continue planning or proceed to `/tasks` if plan complete
- **Context**: Medium, may need research context

### Tasks Phase Resume
- **Required Artifacts**: `spec.md`, `plan.md`, `tasks.md`, possibly `data-model.md`, `contracts/`
- **Dependencies**: Valid spec and plan, design artifacts present
- **Next Action**: Continue tasks refinement or proceed to `/implement T001`
- **Context**: Medium to high, design context important

### Implement Phase Resume
- **Required Artifacts**: `spec.md`, `plan.md`, `tasks.md`, partial code artifacts
- **Dependencies**: Valid spec, plan, and tasks; some tasks may be complete
- **Next Action**: Continue with next incomplete task `/implement [feature] TXXX`
- **Context**: High, code context and patterns important

---

## Error Recovery Integration

Resume functionality integrates with Error Recovery Framework:

### Resume After Error
If resuming from a checkpoint created during error recovery:
- Check if error state still exists in session memory
- Verify error was resolved (status = "Resolved")
- If error still active: Offer to continue recovery or rollback to earlier checkpoint
- Clear error state from Active Focus when resuming

### Checkpoint Rollback
If checkpoint integrity fails:
- Offer to rollback to previous checkpoint in history
- Show checkpoint history (CP-001, CP-002, CP-003, etc.)
- Let user select which checkpoint to restore from
- Apply Strategy 6 (Checkpoint Rollback) from error-recovery.md

### Stale Checkpoint Handling
If checkpoint is suspiciously old (>7 days):
- Warn user about potential staleness
- Recommend running validation:
  - Spec phase: Run `validate-spec.sh`
  - Plan phase: Run `validate-plan.sh`
  - Tasks phase: Verify task list still valid
  - Implement phase: Check test status
- Offer to update checkpoint timestamp if validation passes

---

## Context Optimization for Resume

When resuming, optimize context for efficiency:

### Context Assessment
- **Load Checkpoint Context**: Read context % from checkpoint
- **Estimate Current Context**: Based on artifacts and session memory size
- **Compare**: If current > checkpoint, may need compaction

### Optimization Strategies
- **Summarize Session History**: Keep only essential accomplishments
- **Compact Context Carryover**: Focus on critical decisions only
- **Archive Old Checkpoints**: Keep only last 5 checkpoints in history
- **Prune Manual Notes**: Suggest user review manual notes section

### Resume with Fresh Context
Offer option to resume with "fresh context" mode:
- Load only essential information (phase, artifacts, next action)
- Skip detailed session history (still available in file)
- Start with minimal context for best AI performance
- Recommend when context was high (>60%) at checkpoint

---

## Advanced Resume Features

### Multi-Session Resume
Handle resuming across multiple sessions/days:
- Show timeline of checkpoints
- Highlight gaps in session history
- Summarize overall progress since feature started
- Provide continuity narrative

### Partial Phase Resume
Handle resuming mid-phase (e.g., during plan research):
- Identify exact sub-step within phase
- Restore partial artifacts
- Provide guidance on completing current phase
- Show what's left to do in current phase

### Resume with Context Recovery
If checkpoint context was high:
- Apply context compaction during resume
- Offer to delegate remaining work to subagent
- Restructure context for optimal utilization
- Track context optimization in session memory

---

## Resume Command Variations

### Basic Resume
```bash
/resume user-authentication
```
Resumes from latest checkpoint for the specified feature.

### Auto-Detect Resume
```bash
/resume
```
Auto-detects feature from active workflow marker or offers selection.

### Resume from Specific Checkpoint
```bash
/resume user-authentication --checkpoint CP-003
```
Resumes from a specific checkpoint in history (not latest).

### Resume with Fresh Context
```bash
/resume user-authentication --fresh
```
Resumes with minimal context loading for optimal performance.

### Resume with Validation
```bash
/resume user-authentication --validate
```
Runs full validation before resuming (spec/plan validators, artifact checks).

---

## Integration with Workflow Commands

Each workflow command creates checkpoints automatically:

- **`/spec`**: Creates checkpoint when spec validated and complete
- **`/plan`**: Creates checkpoint when plan validated and complete (also mid-phase checkpoint after research)
- **`/tasks`**: Creates checkpoint when tasks breakdown complete
- **`/implement`**: Creates checkpoint after each task completion and when all tasks complete

Resume command leverages these automatic checkpoints for seamless workflow continuity.

---

## User Communication

### Resume Success Message Format
```
✅ **WORKFLOW RESUMED**

Feature: [feature-name]
Last checkpoint: [timestamp] (X days/hours ago)
Resuming at: [phase-name] phase

What was accomplished:
- [Accomplishment 1 from checkpoint]
- [Accomplishment 2 from checkpoint]
- [Accomplishment 3 from checkpoint]

Current state:
- Phase: [phase-name] ([status])
- Artifacts: [X/Y verified]
- Context: [X%] utilization

Next action: [exact command to run]

Ready to continue! Run the command above.
```

### Resume Failure Message Format
```
❌ **RESUME FAILED**: [Specific reason]

Issue: [What went wrong]
Impact: Cannot resume workflow from this checkpoint

Recovery Options:
1. [Option 1 with command]
2. [Option 2 with command]
3. [Option 3 with command]

Checkpoint Details:
- ID: CP-XXX
- Timestamp: [timestamp]
- Phase: [phase-name]
- Missing artifacts: [list if applicable]

Get help: Review `.bifrost/memory/session.md` for checkpoint history
```

---

## Resume Quality Gates

Before marking resume as successful:

- [ ] **Checkpoint Valid**: All metadata present and parseable
- [ ] **Artifacts Verified**: Critical files exist and are accessible
- [ ] **Dependencies Met**: All prerequisites from checkpoint satisfied
- [ ] **Workflow Consistent**: Active workflow marker matches checkpoint
- [ ] **Session Memory Updated**: Resume action logged in session history
- [ ] **User Informed**: Clear next action provided
- [ ] **Context Reasonable**: Context utilization within acceptable range

---

**Note**: Resume functionality preserves all work and provides seamless continuation of interrupted workflows. Always creates resume entry in session history for tracking.
