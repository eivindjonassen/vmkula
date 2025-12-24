---
description: Execute spec workflow step
---

# Feature Specification: $ARGUMENTS

**⚠️ CRITICAL - CANONICAL PHASE NAMES**: This template uses phase name `spec`. See `templates/standards/workflow-markers.md` for EXACT format requirements. ONLY valid phase names are: `spec`, `plan`, `tasks`, `implement` (NOT "specification", "planning", or "implementation"). These are parsed by TUI and MUST be exact.

**User Input**: `/spec $ARGUMENTS`
**Feature Branch**: `[###-feature-name]` (optional - ask user)
**Created**: [DATE]
**Status**: Draft

## Execution Flow
1. **Feature Name Collection**: Ask user for the feature name (e.g., "club-field-management", "user-authentication") if not clear from description.
2. **✋ MANDATORY STOP**: Ask user: "Would you like to create a new branch for this feature? (y/n)" If yes, create branch as `feature/[feature-name]`. If no, continue on current branch.
3. **Auto-Setup Directory Structure**: Create `specs/[feature-name]/` directory and initialize:
   - `spec.md` with feature name and timestamp
   - `plan.md` placeholder for next phase
   - `tasks.md` placeholder for task breakdown
4. **Set Active Workflow Marker** *(MANDATORY)*: You MUST create the active workflow marker file immediately after creating the directory structure. This is CRITICAL for TUI tracking.
   - Execute: `mkdir -p .bifrost && echo "specs/[feature-name]:spec|" > .bifrost/active-workflow`
   - Verify the file exists with exact content: `specs/[feature-name]:spec|` (no extra whitespace)
   - Format: `path:active-phase|completed-phases` (pipe separates active from completed)
   - The `:spec|` indicates you're actively working on spec with no completed phases yet
   - If this step fails, STOP and report the error
5. **Input Validation**: Parse the user description from the `Input` field. If it's empty, stop with an error: "❌ ERROR: No feature description provided. Please provide a clear feature description."
6. **Concept Extraction**: Extract key concepts: actors (who is using it), actions (what they are doing), data (what is being created/changed), and constraints.
7. **Ambiguity Marking**: For any aspect that is ambiguous or requires an assumption, mark it clearly with `[NEEDS CLARIFICATION: specific question]`.
8. **User Flow Definition**: Define the primary user story and acceptance scenarios based on the description. If a clear user flow cannot be determined, stop with an error: "❌ ERROR: Cannot determine clear user flow from description. Please provide more context about user interactions."
9. **Requirements Generation**: Generate a list of testable, unambiguous functional requirements.
10. **Data Entity Identification**: Identify key data entities if the feature involves data.
11. **Constitutional Compliance**: Review the project's `RULES.md` to ensure the specification aligns with project principles, architecture constraints, and development practices. Note any relevant rules that apply to this feature.
12. **✋ Interactive Clarification Resolution** *(MANDATORY)*: Before finalizing the spec, resolve any ambiguities with the user.
    - Scan the drafted specification for all `[NEEDS CLARIFICATION: ...]` markers
    - Extract each question from the markers
    - If there are 1 or more clarification questions:
      a. Present ALL questions to the user at once in a numbered list
      b. Ask the user: "I have [N] questions about the specification. Please provide answers (or type 'skip' for questions to be determined later):"
      c. Wait for user to provide answers for each question
      d. For each answered question: Replace `[NEEDS CLARIFICATION: question]` with the user's answer
      e. For questions where user says 'skip' or 'later' or 'TBD': Replace `[NEEDS CLARIFICATION: question]` with `[TBD: question - to be determined during planning phase]`
      f. Ensure ALL `[NEEDS CLARIFICATION]` markers are either answered or converted to `[TBD]` markers
     - If there are 0 clarification questions, skip this step and proceed
     - **Goal**: No `[NEEDS CLARIFICATION]` markers should remain after this step
13. **Quality Validation**: Run the Review Checklist below. If any `[NEEDS CLARIFICATION]` markers remain, stop with an error: "❌ ERROR: Specification contains unresolved clarifications. All ambiguities must be resolved before proceeding." If any implementation details (tech stack, libraries) are found, stop with an error: "❌ ERROR: Specification contains implementation details. Focus on WHAT, not HOW."
14. **Auto-Save Specification**: Write the completed specification to `specs/[feature-name]/spec.md`.
15. **Auto-Commit**: Stage and commit specification with message: "Spec: [feature-name] specification completed".
16. **Update Session Memory**: Write to `specs/[feature-name]/session.md` to track session progress:
    - **Feature-Specific Session Isolation**: Each feature maintains its own session file for isolated context tracking across concurrent features
    - **Initialize session file if missing**:
      ```bash
      # Create feature directory and initialize session file if missing
      mkdir -p specs/[feature-name]
      if [[ ! -f specs/[feature-name]/session.md ]]; then
        # Copy session template and customize for this feature
        cp .bifrost/session.md-template specs/[feature-name]/session.md
        # Replace placeholders: {FEATURE_NAME}, {PHASE}, {DATE}, {TIME}
        # AI: Use actual feature name and current date/time values
      fi
      ```
    - **Backward Compatibility Check**: Detect old session format and show migration warning:
      ```bash
      # Warn if old format exists (transition period support)
      OLD_SESSION=".bifrost/memory/session.md"
      NEW_SESSION="specs/[feature-name]/session.md"
      if [[ -f "$OLD_SESSION" && ! -f "$NEW_SESSION" ]]; then
        echo "⚠️  Using legacy session format. Consider migrating: .bifrost/scripts/migrate-session-memory.sh [feature-name]"
      fi
      ```
    - **Update Last Updated date** at top of file with current date (YYYY-MM-DD format)
    - **REPLACE Active Focus section** under `## 🎯 Active Focus` (IMPORTANT: Clear previous feature's context completely):
      - **Feature**: [feature-name]
      - **Phase**: spec
      - **Status**: In Progress
      - Remove all fields from previous feature (Task ID, Description, Progress, etc.)
    - **Add entry to Session History** (under `## 📝 Recent Session Context` → `### Session History (Last 5)`):
      - Format: `**YYYY-MM-DD** - Spec: Created specification for [feature-name]. [Brief 1-line summary of feature purpose].`
      - **CRITICAL - SESSION HISTORY MAINTENANCE (3 STEPS)**:
        1. **FIRST**: Count existing numbered entries (1. 2. 3. etc.) in Session History section
        2. **SECOND**: Add new entry as #1 at the TOP, renumber existing entries (+1 each)
        3. **THIRD**: DELETE ALL entries numbered 6 or higher (keep ONLY entries 1-5)
      - **Validation**: Run `templates/scripts/validate-session-history.sh [feature-name]` to verify
    - **REPLACE Key Decisions** (under `## 🧠 Key Decisions & Context`):
      - Clear previous feature's decisions completely
      - **Context Carryover** → **From Spec**: Add key requirements and scope decisions from specification
    - **REPLACE Progress Tracking** (under `## 📊 Progress Tracking` → `### Feature Progress`):
      - Clear previous feature's progress completely
      - Set **Spec** to "⧗ In Progress"
      - Set **Plan**, **Tasks**, **Implementation** to "○ Not Started"
    - **CLEAR Current Blockers** (under `## ⚠️ Known Issues & Blockers` → `### Current Blockers`):
      - Remove all previous feature's blockers completely
      - Leave subsections "Known Issues" and "Technical Debt" unchanged (project-wide, not feature-specific)
    - **CLEAR Related Files** (under `## 📁 Related Files` → `### Key Files Modified`):
      - Remove all previous feature's files completely
      - Leave "Important References" subsection unchanged if it contains project-wide docs
    - **PRESERVE Cross-Feature Sections** (do NOT clear these):
      - Session History (append-only, keeps last 5)
      - Insights & Learnings (accumulate patterns and learnings)
       - Known Issues (project-wide issues, not feature blockers)
       - Technical Debt (project-wide shortcuts)
17. **Auto-Run Validation** *(MANDATORY)*: Execute validation script to verify spec quality:
    ```bash
    cd [project-root] && .bifrost/scripts/validate-spec.sh specs/[feature-name]/spec.md
    ```
    You MUST execute this command automatically. If validation fails, review and fix issues before proceeding.
18. **Mark Spec as Complete** *(MANDATORY)*: Update the workflow marker to mark spec phase as completed.
    - Execute: `mkdir -p .bifrost && echo "specs/[feature-name]:spec|spec" > .bifrost/active-workflow`
    - This marks spec as both active AND completed (ready to move to next phase)
19. **Update Session Memory (Completion)**: Update `specs/[feature-name]/session.md`:
    - **Update Active Focus section** under `## 🎯 Active Focus`:
      - **Phase**: spec (keep as spec, plan command will change it)
      - **Status**: "Awaiting next action" (spec complete, waiting for /plan)
      - Keep **Feature** unchanged ([feature-name])
    - **Update Progress Tracking** (under `## 📊 Progress Tracking` → `### Feature Progress`):
      - Set **Spec** to "✓ Complete"
    - **REPLACE Next Actions** (under `## 🔄 Next Actions` → `### Immediate Next Steps`):
      - Clear previous feature's next actions completely
      - Replace entire list with: `1. Run \`/plan [feature-name]\` to proceed to planning phase`
20. **Create Checkpoint** *(MANDATORY)*: Add checkpoint to feature session for pause/resume capability:
    - Update `specs/[feature-name]/session.md` under `## 📊 Progress Tracking` → `### Recovery Checkpoints`
    - **Update Latest Checkpoint** (use LOCAL time in format YYYY-MM-DD HH:MM, not UTC):
      ```
      **CP-001** ([current-date] [current-time]): Spec phase complete, validated
        - **Phase**: spec
        - **Status**: Complete
        - **Context**: [estimated-context-%] utilization
        - **Artifacts**: specs/[feature-name]/spec.md (validated)
        - **Dependencies**: None (initial checkpoint)
        - **Next**: `/plan [feature-name]` to proceed to planning phase
      ```
    - **Add to Checkpoint History** (prepend to list, keep only last 5):
      - Same format as Latest Checkpoint
      - Insert at top of Checkpoint History list
      - Remove oldest checkpoint if list exceeds 5 entries
    - This checkpoint enables `/resume` command to restore workflow from this point
21. **✋ MANDATORY STOP**: End here with message: "🚦 **SPECIFICATION COMPLETE** - Run `/plan [feature-name]` to proceed to planning phase."

---

## Error Recovery Protocol

*Reference: `templates/standards/error-recovery.md` for complete framework*

### Spec Phase Error Handling

**Common Errors & Recovery Strategies**:

1. **❌ Insufficient Feature Description** (Error Category: User Input)
   - **Detection**: Step 5 - Empty or vague description
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Stop immediately with clear error message
     - Ask user for specific missing information (actors, actions, goals)
     - Show example of complete description
     - Retry spec generation with enhanced input

2. **❌ Unclear User Flow** (Error Category: Validation Failure)
   - **Detection**: Step 8 - Cannot determine clear user interactions
   - **Recovery**: Strategy 4 (Alternative Approach)
   - **Action**:
     - Present drafted scenarios to user for feedback
     - Offer multiple interpretations if ambiguous
     - Iterate with user until clear user story emerges
     - Document agreed user flow in spec

3. **❌ Unresolved Clarification Markers** (Error Category: Validation Failure)
   - **Detection**: Step 13 - `[NEEDS CLARIFICATION]` markers remain after interactive resolution
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Collect all remaining markers
     - Present as numbered list to user
     - Allow user to answer or mark as `[TBD]` for later
     - Verify all `[NEEDS CLARIFICATION]` converted to answers or `[TBD]`
     - Re-validate before proceeding

4. **❌ Implementation Details Detected** (Error Category: Validation Failure)
   - **Detection**: Step 13 - Tech stack, libraries, or "how" details found in spec
   - **Recovery**: Strategy 1 (Immediate Retry with Corrections)
   - **Action**:
     - Identify and highlight implementation details
     - Strip all "how" content, preserve only "what"
     - Rewrite affected sections focusing on requirements
     - Re-validate for purity (WHAT not HOW)

5. **❌ Git Branch Creation Failure** (Error Category: Tool Failure)
   - **Detection**: Step 2 - Branch already exists or git error
   - **Recovery**: Strategy 4 (Alternative Approach)
   - **Action**:
     - Offer alternatives: continue on existing branch, use different name, or skip branching
     - If continuing existing branch, verify it's correct feature
     - Update workflow marker appropriately
     - Proceed with user's choice

6. **❌ Workflow Marker Write Failure** (Error Category: Tool Failure)
   - **Detection**: Step 4 - Cannot create `.bifrost/active-workflow` file
   - **Recovery**: Strategy 4 (Alternative Approach)
   - **Action**:
     - Check file permissions and directory structure
     - Attempt to create `.bifrost/` directory if missing
     - Retry marker creation
     - If persistent failure, warn user and continue (TUI tracking unavailable)

7. **❌ Session Memory Write Failure** (Error Category: Tool Failure)
   - **Detection**: Step 17 - Cannot write to `specs/[feature-name]/session.md`
   - **Recovery**: Strategy 5 (Graceful Degradation)
   - **Action**:
     - Verify `specs/[feature-name]/` directory exists
     - Check file permissions
     - Attempt to create missing directory/file
     - If persistent failure, warn user (session continuity unavailable) but proceed with spec

8. **❌ Validation Script Failure** (Error Category: Tool Failure)
   - **Detection**: Step 17 - `validate-spec.sh` not found or not executable
   - **Recovery**: Strategy 5 (Graceful Degradation)
   - **Action**:
     - Warn user that validation unavailable
     - Perform manual quality checklist verification
     - Suggest running `bifrost-admin.py` to update scripts
     - Proceed if manual validation passes

### Error State Tracking

When errors occur during spec phase, update session memory:

```markdown
## 🎯 Active Focus
- **Feature**: [feature-name]
- **Phase**: spec
- **Status**: Error Recovery
- **Error Type**: [Category from error-recovery.md]
- **Recovery Strategy**: [Strategy name]
- **Recovery Action**: [Specific action being taken]

## ⚠️ Known Issues & Blockers
### Current Blockers
- **[Error Type] (2025-XX-XX)**: [Brief description of error]
  - **Recovery**: [Strategy being applied]
  - **Status**: [In Progress/Resolved]
  - **Next**: [What needs to happen to resolve]
```

After successful recovery, update status to "In Progress" and clear blocker.

### Recovery Quality Gates

Before proceeding after error recovery:

- [ ] **Error Resolved**: Root cause addressed and verified
- [ ] **State Consistent**: Workflow marker and session memory in sync
- [ ] **Artifacts Valid**: spec.md exists and passes validation
- [ ] **User Informed**: User understands what happened and resolution
- [ ] **Recovery Logged**: Error and recovery tracked in session memory

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
*As a [user type], I want to [perform an action] so that I can [achieve a goal].*

### Acceptance Scenarios
1.  **Given** [initial state], **When** [action], **Then** [expected outcome].
2.  **Given** [error state], **When** [same action], **Then** [expected error handling].

### Edge Cases & Unhappy Paths
- What happens when [a boundary condition is met]?
- How does the system handle [an invalid input or error scenario]?
- What are the permissions required? [NEEDS CLARIFICATION: Specify roles if not obvious].

## Requirements *(mandatory)*

### Functional Requirements
- **FR-001**: The system MUST [provide a specific, testable capability].
- **FR-002**: Users MUST be able to [perform a key interaction].
- **FR-003**: The system MUST [adhere to a specific data rule or constraint].

*Example of an ambiguous requirement:*
- **FR-004**: The system MUST integrate with [NEEDS CLARIFICATION: Which third-party service? What is the API contract?].

### Key Entities *(optional, include if feature involves data)*
- **[Entity Name]**: Represents [what the entity is]. Key attributes are: [list attributes without types].

---

## Review & Acceptance Checklist
*This checklist is verified by the agent during the `Execution Flow`.*

- [ ] **Clarity**: The spec is written for a non-technical audience.
- [ ] **Completeness**: All mandatory sections are filled, and there are no remaining `[NEEDS CLARIFICATION]` markers. (`[TBD]` markers are acceptable for items to be determined during planning phase.)
- [ ] **Purity**: The spec focuses purely on **WHAT** is needed, not **HOW** to build it. There are no implementation details (languages, frameworks, databases, etc.).
- [ ] **Testability**: All functional requirements are specific, measurable, and can be turned into a failing test case.