# Error Recovery Framework

**Version**: 1.0
**Last Updated**: 2025-10-10
**Purpose**: Standardized error handling and recovery protocols for Bifrost workflows

## Overview

This framework defines how Bifrost workflows handle errors, preserve context, and recover from failures without losing progress. All workflow commands (`/spec`, `/plan`, `/tasks`, `/implement`) follow these protocols to ensure robust, resumable development workflows.

## Core Principles

1. **Preserve Context**: Never lose work progress or critical context during errors
2. **Clear Communication**: Provide actionable error messages with recovery paths
3. **Graceful Degradation**: Offer alternatives when primary approaches fail
4. **State Persistence**: Track recovery checkpoints in session memory
5. **User Control**: Allow users to intervene and guide recovery when needed

---

## Error Categories

### 1. Validation Failures
**Occurs When**: Spec/plan validation scripts fail, quality gates not met, or constitutional violations detected

**Symptoms**:
- `validate-spec.sh` returns non-zero exit code
- `validate-plan.sh` detects missing required sections
- `[NEEDS CLARIFICATION]` markers remain in final output
- Implementation details found in spec phase

**Impact**: Medium - Work complete but not committable

### 2. Complex Scope
**Occurs When**: Task scope exceeds manageable single-agent limits

**Symptoms**:
- Large codebase (>50 files) requires deep exploration
- Research phase requires extensive exploration
- Complex implementation spanning multiple systems

**Impact**: Medium - Consider subagent delegation for efficiency

**Note**: Context window management is handled automatically by the CLI's auto-compact feature. Focus on task scope and complexity when deciding delegation.

### 3. Tool Failures
**Occurs When**: External tools, scripts, or commands fail unexpectedly

**Symptoms**:
- Git commands fail (branch already exists, merge conflicts)
- Test execution fails (missing dependencies, configuration errors)
- Validation scripts not found or not executable
- File system operations fail (permissions, disk space)

**Impact**: Medium to High - Workflow blocked until tool issue resolved

### 4. Dependency Issues
**Occurs When**: Required files, packages, or system dependencies missing

**Symptoms**:
- Spec/plan files not found when expected
- Required npm/pip packages not installed
- Technology stack incompatible with feature requirements

**Impact**: High - Cannot proceed without resolving dependencies

### 5. Workflow State Errors
**Occurs When**: Workflow marker or session memory in inconsistent state

**Symptoms**:
- Active workflow marker missing or malformed
- Session memory out of sync with actual progress
- Phase transitions attempted out of order

**Impact**: Medium - Can cause incorrect TUI display or workflow confusion

### 6. User Interruptions
**Occurs When**: User cancels operation or provides unexpected input

**Symptoms**:
- User declines branch creation or clarification questions
- Ctrl+C during long-running operations
- User provides invalid or incomplete responses

**Impact**: Low to Medium - Depends on when interruption occurred

---

## Recovery Strategies

### Strategy 1: Immediate Retry with Corrections
**Use For**: Validation failures, minor tool failures, user input errors

**Protocol**:
1. **Preserve Current State**: Save all work-in-progress to temporary checkpoint
2. **Identify Root Cause**: Parse error output to identify specific failure reason
3. **Show Clear Error**: Present error with specific issue and required fix
4. **Offer Corrections**: Provide actionable steps or ask for user input
5. **Retry Operation**: Re-run validation/operation with corrections applied
6. **Verify Success**: Confirm error resolved before proceeding

**Example Flow**:
```
❌ ERROR: Specification validation failed
  - Issue: 3 unresolved [NEEDS CLARIFICATION] markers found
  - Location: specs/user-auth/spec.md lines 42, 67, 89

🔄 Recovery: Resolving clarifications...
  1. Line 42: "Which authentication method?" → User response: "OAuth2 with JWT"
  2. Line 67: "Session timeout duration?" → User response: "30 minutes"
  3. Line 89: "Password requirements?" → User response: "Min 8 chars, 1 uppercase, 1 number"

✓ Retrying validation... Success!
```

### Strategy 2: Subagent Delegation
**Use For**: Large codebase research (>50 files), complex multi-system tasks, specialized analysis

**Protocol**:
1. **Recognize Complexity**: Identify when task exceeds reasonable context limits
2. **Define Delegation Scope**: Specify clear research questions or implementation tasks
3. **Create Specialized Agent**: Use Task tool with focused prompt and context
4. **Provide Handoff Context**: Give subagent minimal essential context
5. **Coordinate Results**: Integrate subagent findings back into main workflow
6. **Track Delegation**: Record subagent tasks in session memory

**Example Flow**:
```
🤖 DELEGATING: Large codebase (75+ files) - Creating Research Agent...

Agent Task: Explore authentication patterns in existing codebase
Scope:
  - Identify existing auth libraries and patterns
  - Document JWT implementation approach
  - Find reusable authentication components

✓ Research Agent created - Awaiting results...
[Agent completes research]
✓ Integrated findings - Resuming planning...
```

### Strategy 3: Alternative Approach Selection
**Use For**: Tool failures with available workarounds, blocked primary paths

**Protocol**:
1. **Identify Blocker**: Determine what is preventing primary approach
2. **Enumerate Alternatives**: List viable alternative approaches
3. **Evaluate Trade-offs**: Consider each alternative's pros/cons
4. **Select Alternative**: Choose best alternative given circumstances
5. **Execute Alternative**: Proceed with alternative approach
6. **Document Decision**: Record why alternative was chosen

**Example Flow**:
```
❌ ERROR: Git branch creation failed - branch 'feature/user-auth' already exists

🔄 Alternative Approaches:
  1. Continue on existing branch (user-auth work already in progress)
  2. Create branch with different name (feature/user-auth-v2)
  3. Delete existing branch and recreate (destructive)

User choice: [1] Continue on existing branch
✓ Proceeding with current branch - Updating workflow marker...
```

### Strategy 4: Graceful Degradation
**Use For**: Non-critical failures, optional features unavailable, acceptable compromises

**Protocol**:
1. **Classify Failure**: Determine if failure is critical or acceptable
2. **Define Minimum Viable**: Identify minimum requirements for proceeding
3. **Communicate Trade-off**: Clearly explain what functionality is lost
4. **Offer User Choice**: Let user decide if acceptable or requires fixing
5. **Proceed or Block**: Continue with degradation or stop for fix
6. **Track Limitation**: Record degradation in session memory

**Example Flow**:
```
⚠️ WARNING: Test execution unavailable (npm test script not found)

Degradation Options:
  1. Continue without test verification (tests created but not verified)
  2. Stop and configure test script (ensures tests work)

User choice: [1] Continue without verification
✓ Proceeding - Tests created but marked as unverified in session memory...
```

### Strategy 5: Checkpoint Rollback
**Use For**: Corrupted state, severe errors mid-phase, user-requested restart

**Protocol**:
1. **Detect Corruption**: Identify when state is irrecoverably broken
2. **Find Last Checkpoint**: Locate most recent valid checkpoint in session memory
   - Read `.bifrost/memory/session.md` under `## 📊 Progress Tracking` → `### Recovery Checkpoints`
   - Check **Latest Checkpoint** for most recent recovery point
   - If Latest Checkpoint corrupted, fall back to **Checkpoint History** (last 5 checkpoints)
   - Parse checkpoint metadata: phase, status, artifacts, dependencies, next command
3. **Confirm Rollback**: Warn user about work loss and get confirmation
   - Show checkpoint timestamp and description
   - List artifacts that will be lost (work since checkpoint)
   - Display next command from checkpoint for clarity
4. **Restore State**: Revert workflow marker, session memory, and artifacts
   - Update workflow marker: `echo "specs/[feature]:[phase]|[completed]" > .bifrost/active-workflow`
   - Restore session memory Active Focus to checkpoint state
   - Verify all artifacts listed in checkpoint exist and are valid
5. **Clean Partial Work**: Remove any corrupted or partial files
   - Identify files created after checkpoint timestamp
   - Ask user permission before deleting work-in-progress files
   - Preserve backup of partial work in `.bifrost/rollback-backup/[timestamp]/`
6. **Resume from Checkpoint**: Restart from last valid state
   - Use `/resume` command with `--checkpoint CP-XXX` flag if specific checkpoint selected
   - Or use checkpoint's "Next" field to show user exact command to continue
   - Log rollback action in session history

**Checkpoint Format** (from session.md):
```markdown
**CP-003** (2025-10-10 16:20): Plan validated, ready for tasks
  - **Phase**: plan
  - **Status**: Complete
  - **Artifacts**: plan.md, research.md, data-model.md, contracts/
  - **Dependencies**: Spec validated, technical context resolved
  - **Next**: `/tasks user-auth` to break down into tasks
```

**Example Flow**:
```
❌ CRITICAL ERROR: Workflow state corrupted (session.md malformed)

Checkpoint History:
  CP-005 (2025-10-10 18:30): Phase 2 tests complete [CORRUPTED]
  CP-004 (2025-10-10 17:00): Tasks breakdown complete ✓ VALID
  CP-003 (2025-10-10 16:20): Plan validated ✓ VALID

Last Valid Checkpoint: CP-004 - Tasks breakdown complete (2025-10-10 17:00)
Rollback Impact: Will lose 2 implementation tasks (T001, T002 partial work)

Confirm rollback to CP-004? (y/n): y
✓ Backing up partial work to .bifrost/rollback-backup/20251010-183000/...
✓ Rolling back to tasks phase completion...
✓ Restored workflow marker: specs/user-auth:tasks|spec,plan,tasks
✓ Restored session memory from CP-004
✓ Cleaned corrupted checkpoint CP-005
✓ Ready to resume with `/implement user-auth T001`
```

**Integration with `/resume` Command**:
```bash
# Resume from latest checkpoint (automatic)
/resume user-auth

# Resume from specific checkpoint (rollback scenario)
/resume user-auth --checkpoint CP-004

# Resume with validation (verify checkpoint integrity)
/resume user-auth --validate
```

---

## Session Memory Integration

### Error State Tracking

When errors occur, update `.bifrost/memory/session.md` to track recovery state:

```markdown
## 🎯 Active Focus
- **Feature**: user-authentication
- **Phase**: plan
- **Status**: Error Recovery
- **Error Type**: Complex Scope
- **Recovery Strategy**: Subagent Delegation
- **Recovery Action**: Research agent created for auth patterns exploration

## ⚠️ Known Issues & Blockers
### Current Blockers
- **Complex Scope (2025-10-10)**: Large codebase (75+ files) during planning phase
  - **Recovery**: Created research subagent to explore authentication patterns
  - **Status**: Awaiting subagent results
  - **Next**: Integrate findings and resume planning
```

### Recovery Checkpoints

Add checkpoints at key workflow milestones:

```markdown
## 📊 Progress Tracking
### Recovery Checkpoints
- **CP-001** (2025-10-10 14:30): Spec phase complete, validated
- **CP-002** (2025-10-10 15:45): Planning research complete, design starting
- **CP-003** (2025-10-10 16:20): Plan validated, ready for tasks
```

### Recovery History

Track successful recoveries for learning:

```markdown
## 💡 Insights & Learnings
### Recovery Patterns
- **Complex Scope → Subagent Delegation**: Used during planning phase for large codebase exploration (50+ files). Delegated to research agent. Pattern: Delegate when exploration scope exceeds 50 files.
- **Validation Failure → Immediate Retry**: Spec validation failed due to unresolved clarifications. Quick user Q&A resolved all issues in single retry.
```

---

## Phase-Specific Error Handling

### Spec Phase Errors

**Common Errors**:
- User provides insufficient description
- Cannot determine clear user flow
- Unresolved clarification markers remain
- Implementation details accidentally included

**Recovery Approach**:
```markdown
1. **Insufficient Description**:
   - Stop immediately with clear error
   - Ask user for specific missing information
   - Show what aspects need clarification
   - Retry spec generation with enhanced input

2. **Unclear User Flow**:
   - Present drafted scenarios to user
   - Ask user to confirm or correct
   - Iterate until clear user story emerges
   - Document final user story in spec

3. **Unresolved Clarifications**:
   - Collect all [NEEDS CLARIFICATION] markers
   - Present as numbered list to user
   - Allow user to answer or mark TBD
   - Verify all markers resolved before commit

4. **Implementation Details**:
   - Detect tech stack mentions, library names
   - Strip implementation details from spec
   - Preserve pure "what" without "how"
   - Re-validate before proceeding
```

### Plan Phase Errors

**Common Errors**:
- Spec file not found (out-of-order execution)
- Context overflow during research
- Constitution violations detected
- Missing required design artifacts

**Recovery Approach**:
```markdown
1. **Missing Spec File**:
   - Stop with clear error and guidance
   - Show expected file path
   - Suggest running /spec first
   - Do not attempt to create plan without spec

2. **Large Codebase**:
   - Apply Strategy 2 (Subagent Delegation) for >50 files
   - Create research agent for systematic exploration
   - Integrate findings into planning context

3. **Constitution Violations**:
   - Identify specific rule violations
   - Check Complexity Tracking for justification
   - If no valid justification, stop with error
   - Offer alternatives that comply with rules

4. **Missing Design Artifacts**:
   - Identify which artifacts missing (data-model.md, contracts/, tests)
   - Complete missing artifacts before proceeding
   - Validate all artifacts present
   - Verify quality before marking plan complete
```

### Tasks Phase Errors

**Common Errors**:
- Plan file not found (out-of-order execution)
- Task numbering conflicts or gaps
- TDD ordering violations (impl before test)
- Parallel task marking incorrect

**Recovery Approach**:
```markdown
1. **Missing Plan File**:
   - Stop with clear error and guidance
   - Show expected file path
   - Suggest running /plan first
   - Do not attempt to create tasks without plan

2. **Task Numbering Issues**:
   - Detect conflicts or gaps automatically
   - Renumber tasks sequentially
   - Verify no duplicates
   - Update all task references

3. **TDD Violations**:
   - Scan task list for test→impl ordering
   - Reorder tasks to enforce TDD (tests before implementation)
   - Mark Phase 2 (tests) complete before Phase 3 (impl)
   - Add clear phase boundaries

4. **Parallel Marking Errors**:
   - Review each [P] task for true independence
   - Verify no shared file modifications
   - Check for dependency relationships
   - Correct parallel markers as needed
```

### Implement Phase Errors

**Common Errors**:
- Task file or task ID not found
- Tests fail unexpectedly
- Implementation exceeds task scope
- Git commit fails (conflicts, hooks)

**Recovery Approach**:
```markdown
1. **Missing Task/ID**:
   - Stop with clear error
   - Show available task IDs
   - Verify tasks.md exists
   - Suggest correct task ID format

2. **Test Failures**:
   - Phase 2: Expected failure → verify error message clear and actionable
   - Phase 3: Unexpected failure → review implementation, offer retry or debugging
   - Phase 4: Validation failure → identify regression, fix, re-run suite
   - Always show test output for user diagnosis

3. **Scope Creep**:
   - Detect when implementation extends beyond single task
   - Stop and review task boundaries
   - Offer to split into multiple tasks
   - Complete current task narrowly, defer extensions

4. **Git Commit Failures**:
   - Merge conflicts: Show conflict files, pause for user resolution
   - Pre-commit hooks: Review hook output, fix issues, retry commit
   - Permissions: Check file/directory permissions, suggest fix
   - Always preserve uncommitted work for recovery
```

---

## Error Communication Standards

### Error Message Format

All error messages follow this structure:

```
❌ ERROR: [Clear one-line description of what failed]

Details:
  - [Specific detail 1]
  - [Specific detail 2]
  - [Specific detail 3]

Impact: [What this prevents from proceeding]

🔄 Recovery Options:
  1. [Primary recovery approach] (recommended)
  2. [Alternative approach 1]
  3. [Alternative approach 2]

Next Steps: [Clear action for user to take]
```

### Warning Message Format

For non-critical issues:

```
⚠️ WARNING: [Clear one-line description of issue]

Context: [Why this matters]

Recommendation: [Suggested action]

Proceeding: [What will happen if not addressed]
```

### Success After Recovery Format

```
✓ RECOVERED: [What was fixed]

Recovery Method: [Which strategy was used]
Recovery Time: [How long it took]
State Restored: [What checkpoint/state was restored]

Resuming: [What happens next]
```

---

## Quality Gates for Error Recovery

Before resuming workflow after error recovery:

- [ ] **State Consistency**: Workflow marker, session memory, and files in sync
- [ ] **Checkpoint Valid**: Current state can serve as valid recovery checkpoint
- [ ] **Error Logged**: Error and recovery tracked in session memory
- [ ] **User Informed**: User understands what happened and what was recovered
- [ ] **Lessons Captured**: Recovery patterns documented for future reference

---

## Integration with Existing Workflows

### Workflow Marker Updates During Recovery

When recovering from errors:

```bash
# Preserve active phase but track recovery
echo "specs/feature-name:plan|spec" > .bifrost/active-workflow
# Phase stays same, completed phases preserved

# Add recovery indicator in session memory (not in marker file)
# marker file keeps standard format for compatibility
```

### Session Memory Updates During Recovery

```markdown
## 🎯 Active Focus
- **Status**: Error Recovery → Idle (after recovery)
- **Error Type**: [Category from this framework]
- **Recovery Strategy**: [Strategy name from this framework]
- **Recovery Action**: [Specific action taken]

## 📝 Recent Session Context
### Session History (Last 5)
- **2025-10-10** - Error Recovery: Recovered from complex scope issue during planning using subagent delegation for large codebase.
```

### Validation Script Integration

Validation scripts should return structured error data:

```bash
# validate-spec.sh example
if [ $ERRORS -gt 0 ]; then
    echo "ERROR_TYPE: Validation Failure"
    echo "ERROR_COUNT: $ERRORS"
    echo "ERROR_CATEGORY: Spec Quality"
    echo "RECOVERY_STRATEGY: Immediate Retry"
    exit 1
fi
```

---

## Testing Error Recovery

### Simulated Error Scenarios

Test each error category:

1. **Validation Failures**: Intentionally leave `[NEEDS CLARIFICATION]` markers
2. **Complex Scope**: Test with large codebase (50+ files)
3. **Tool Failures**: Test with non-existent branch, missing scripts
4. **Dependency Issues**: Test with missing spec/plan files
5. **Workflow State Errors**: Test with malformed workflow marker
6. **User Interruptions**: Test with Ctrl+C at various workflow stages

### Recovery Verification

For each recovery strategy:

- [ ] Error detected correctly and immediately
- [ ] Clear, actionable error message shown
- [ ] Recovery strategy applied successfully
- [ ] State preserved or restored correctly
- [ ] Session memory updated with recovery info
- [ ] Workflow resumed without data loss
- [ ] User informed of recovery actions

---

## Future Enhancements

### Planned Improvements

1. **Automatic Checkpoint Creation**: Auto-save checkpoints at phase boundaries
2. **Recovery Analytics**: Track common error patterns and recovery success rates
3. **Scope Prediction**: Predict complexity before starting large tasks
4. **Smart Retry Logic**: Learn from recovery patterns to improve retry strategies
5. **Recovery History Dashboard**: Visual history of errors and recoveries
6. **Cross-Session Recovery**: Resume interrupted workflows across agent sessions

### Extension Points

- **Custom Recovery Handlers**: Project-specific recovery logic
- **Recovery Plugins**: Community-contributed recovery strategies
- **Error Pattern Library**: Shared knowledge base of error solutions
- **Recovery Metrics**: Track MTTR (Mean Time To Recovery) per error type

---

## References

- **12-Factor Agents**: Factor #9 (Plan for failure, engineer for recovery)
- **Session Memory System**: `.bifrost/memory/session.md` structure
- **Workflow Tracking**: `.bifrost/active-workflow` format
- **Validation Scripts**: `validate-spec.sh`, `validate-plan.sh`
- **Context Management**: Advanced Context Engineering (ACE) framework
