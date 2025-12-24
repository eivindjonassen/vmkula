# Workflow Marker Standards

**CRITICAL**: This document defines the EXACT format for workflow markers and phase names. These are parsed by scripts and MUST be followed precisely.

## Canonical Phase Names

**ONLY these four phase names are valid:**
- `spec` (NOT "specification")
- `plan` (NOT "planning")
- `tasks` (NOT "task breakdown")
- `implement` (NOT "implementation" or "implementing")

**Where These Names Must Be Used:**

1. **`.bifrost/active-workflow` file** (CRITICAL)
   - Format: `specs/[feature-name]:[phase]|[completed-phases]`
   - Example: `specs/members-and-groups:implement|spec,plan,tasks`
   - Phase values MUST be one of: `spec`, `plan`, `tasks`, `implement`

2. **`.bifrost/memory/session.md` - Active Focus section**
   - Field: `- **Phase**: [phase]`
   - MUST use canonical name (e.g., `implement` not `implementation`)
   - This is displayed in TUI pane 0

3. **Checkpoint entries in session.md**
   - Field: `- **Phase**: [phase]`
   - MUST use canonical name

## Active Workflow Marker Format

**EXACT FORMAT** (parsed by TUI):
```
specs/[feature-name]:[active-phase]|[completed-phases-comma-separated]
```

**Examples:**
```
specs/members-and-groups:spec|
specs/members-and-groups:spec|spec
specs/members-and-groups:plan|spec
specs/members-and-groups:plan|spec,plan
specs/members-and-groups:tasks|spec,plan
specs/members-and-groups:tasks|spec,plan,tasks
specs/members-and-groups:implement|spec,plan,tasks
specs/members-and-groups:implement|spec,plan,tasks,implement
```

**Rules:**
1. NO spaces anywhere
2. Feature path format: `specs/[feature-name]` (exactly this format)
3. Colon separates path from phase
4. Pipe separates phase from completed list
5. Completed phases: comma-separated, NO spaces
6. Completed phases must be in order: `spec,plan,tasks,implement`
7. Active phase must be one of the canonical four

## TUI Display Logic

The bifrost-tui uses these phase names to display:
```
● spec → ● plan → ● tasks → ◐ implement
```

**Status Indicators:**
- `●` (green) = Phase in completed list
- `◐` (yellow) = Active phase (from :[phase] field)
- `○` (gray) = Not started

**This ONLY works if phase names match exactly!**

## Common Mistakes to Avoid

❌ **WRONG:**
```
specs/members-and-groups:implementation|spec,plan,tasks
- **Phase**: implementation
```

✅ **CORRECT:**
```
specs/members-and-groups:implement|spec,plan,tasks
- **Phase**: implement
```

❌ **WRONG:**
```
specs/members-and-groups:implement|spec, plan, tasks
```
(spaces in completed list)

✅ **CORRECT:**
```
specs/members-and-groups:implement|spec,plan,tasks
```

## Validation Commands

Commands MUST verify the marker format before proceeding:

```bash
# Verify format
cat .bifrost/active-workflow

# Should output exactly:
# specs/[feature-name]:[phase]|[completed]
```

## Template Instructions

Every workflow command template MUST:

1. **Set marker at start** with in-progress indicator
2. **Update marker on completion** with phase added to completed list
3. **Verify marker** after each write
4. **Use canonical phase names** in ALL session.md updates

## Recovery from Incorrect Markers

If a marker is malformed:

1. **Detect the issue**: TUI will show incorrect status
2. **Fix manually**:
   ```bash
   echo "specs/[feature-name]:[correct-phase]|[correct-completed]" > .bifrost/active-workflow
   ```
3. **Refresh TUI**: Press `r` in pane 0

---

**Remember:** These are not suggestions - they are EXACT format requirements parsed by bash scripts. Any deviation will break the TUI display.
