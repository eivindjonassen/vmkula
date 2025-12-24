# Bifrost Template Scripts

Utility scripts for validating and maintaining Bifrost templates and workflows.

## Available Scripts

### Document Validation

#### `validate-spec.sh`
Validates specification documents.

**Usage:**
```bash
./templates/scripts/validate-spec.sh specs/my-feature/spec.md
```

#### `validate-plan.sh`
Validates plan documents.

**Usage:**
```bash
./templates/scripts/validate-plan.sh specs/my-feature/plan.md [RULES.md]
```

#### `validate-session-history.sh`
Validates session history format and entry limits.

**Usage:**
```bash
./templates/scripts/validate-session-history.sh feature-name [--fix]
```

### Workflow Management

#### `command-compliance.sh`
Wrapper for running all validators.

**Usage:**
```bash
# Validate specific file
./templates/scripts/command-compliance.sh specs/my-feature/spec.md

# Validate all specs and plans
./templates/scripts/command-compliance.sh

# Quiet mode (for CI/CD)
BIFROST_QUIET=1 ./templates/scripts/command-compliance.sh
```

### Session Management

#### `migrate-session-memory.sh`
Migrates session memory from old format to new feature-specific format.

**Usage:**
```bash
./templates/scripts/migrate-session-memory.sh feature-name
```

#### `rollup-session-learnings.sh`
Extracts learnings from completed feature sessions into project session.

**Usage:**
```bash
./templates/scripts/rollup-session-learnings.sh feature-name
```

### Context Management

#### `context-monitor.sh`
Monitors context usage and provides optimization suggestions.

**Usage:**
```bash
./templates/scripts/context-monitor.sh
```

### Pattern Management

#### `apply-pattern.sh`
Applies discovered patterns to codebase.

**Usage:**
```bash
./templates/scripts/apply-pattern.sh pattern-name target-file
```

### Dependency Management

#### `check-dependencies.sh`
Validates project dependencies and checks for vulnerabilities.

**Usage:**
```bash
./templates/scripts/check-dependencies.sh
```

#### `log-compliance.sh`
Checks logging compliance with project standards.

**Usage:**
```bash
./templates/scripts/log-compliance.sh
```

---

## Integration Examples

### Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit

# Validate specs and plans
BIFROST_QUIET=1 ./.bifrost/scripts/command-compliance.sh || exit 1
```

### CI/CD Pipeline
```yaml
# .github/workflows/validate.yml
name: Validate Specs and Plans

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Validate all specs and plans
        run: BIFROST_QUIET=1 ./.bifrost/scripts/command-compliance.sh
```

### Makefile Integration
```makefile
.PHONY: validate-all
validate-all:
	@echo "Validating specs and plans..."
	@BIFROST_QUIET=1 ./.bifrost/scripts/command-compliance.sh
```

---

## Troubleshooting

### "Permission denied" error
Make scripts executable:
```bash
chmod +x templates/scripts/*.sh
```

### "Command not found" error
Run from project root or use full path:
```bash
cd /path/to/bifrost
./templates/scripts/validate-implement-template.sh templates/commands/implement.md
```

### Validation fails on valid template
Check that template follows required structure:
1. Required sections are present
2. Step numbering is sequential
3. Template variables use correct format `[variable-name]`
4. Workflow markers are referenced

---

## Contributing

When adding new validation scripts:

1. Follow existing naming pattern: `validate-{target}.sh`
2. Include usage instructions in header comment
3. Use color-coded output (RED, YELLOW, GREEN)
4. Return proper exit codes (0=pass, 1=fail)
5. Support quiet mode via `BIFROST_QUIET` env var
6. Add entry to this README
7. Add integration example if applicable

---

## Script Dependencies

All scripts require:
- Bash 3.2+ (macOS compatible)
- Standard Unix utilities (grep, sed, awk)
- No external dependencies

Some scripts may require:
- git (for workflow marker scripts)
- project-specific tools (for dependency checks)

