---
description: Execute update-rules workflow step
---

# Update Rules Template

## Purpose
Analyze the current codebase to discover patterns and enhance the existing RULES.md with concrete standards based on actual implementation.

## Execution Flow

1. **Analyze Current RULES.md**
   - Read existing RULES.md to understand current foundation
   - Identify sections marked for discovery (<!-- Will be populated... -->)

2. **Discover Codebase Patterns**
   - Scan project structure and file organization
   - Identify testing patterns and frameworks in use
   - Analyze error handling approaches
   - Document API patterns and conventions
   - Find configuration and tooling choices

3. **Extract Concrete Standards**
   - Convert discovered patterns into actionable rules
   - Provide code examples from the actual codebase
   - Identify inconsistencies that need standardization

4. **Update RULES.md**
   - Fill in "To Be Discovered" sections with actual patterns
   - Add specific examples from the codebase
   - Maintain evolution history
   - Suggest areas that still need team decisions

## Analysis Areas

### Code Organization Patterns
```bash
# Directory structure analysis
find . -type d -name "src" -o -name "lib" -o -name "components" -o -name "utils" | head -20

# File naming conventions
find . -name "*.ts" -o -name "*.js" -o -name "*.tsx" -o -name "*.jsx" | head -20 | xargs ls -la
```

### Testing Strategy Discovery
```bash
# Find test files and frameworks
find . -name "*.test.*" -o -name "*.spec.*" -o -name "__tests__" | head -10
grep -r "import.*from.*test" --include="*.json" package.json */package.json 2>/dev/null
```

### Error Handling Patterns
```bash
# Look for error handling approaches
grep -r "throw new Error" --include="*.ts" --include="*.js" . | head -5
grep -r "Result<" --include="*.ts" . | head -5
grep -r "try.*catch" --include="*.ts" --include="*.js" . | head -5
```

### API Conventions
```bash
# Find API-related files
find . -name "*api*" -o -name "*router*" -o -name "*controller*" -o -name "*.graphql" | head -10
grep -r "export.*function" --include="*api*" --include="*router*" . | head -5
```

### Configuration & Tooling
```bash
# Find config files
find . -maxdepth 2 -name "*.config.*" -o -name ".*rc*" -o -name "*.json" | grep -E "(tsconfig|eslint|prettier|vite|webpack|rollup)"
```

## RULES.md Enhancement Template

Replace placeholder sections with discovered patterns:

### Code Organization (Discovered)
```markdown
### Code Organization
Based on current codebase structure:

#### Directory Structure
- `/src/components/` - React components with co-located tests
- `/src/utils/` - Shared utility functions
- `/src/hooks/` - Custom React hooks
- [Document actual structure found]

#### File Naming Conventions
- Components: PascalCase (e.g., `UserProfile.tsx`)
- Utilities: camelCase (e.g., `formatDate.ts`)
- Tests: `ComponentName.test.tsx`
- [Document actual patterns found]
```

### Error Handling (Discovered)
```markdown
### Error Handling
Current patterns found in codebase:

#### Approach
- [Result types / Traditional exceptions / Mixed approach]

#### Examples from Codebase
```typescript
// Example found in src/utils/validation.ts:
[Include actual code example]
```

#### Standards
- [Define standards based on discovered patterns]
```

### Testing Strategy (Discovered)
```markdown
### Testing Strategy
Current testing setup:

#### Framework
- **Unit Tests**: [Jest/Vitest/etc. - what was found]
- **E2E Tests**: [Playwright/Cypress/etc. - if found]

#### Patterns Found
- Test files located: [co-located / separate test directory]
- Naming convention: [*.test.* / *.spec.*]
- Mock strategy: [what mocking patterns were found]

#### Coverage Requirements
- [Based on existing test coverage, suggest standards]
```

## Evolution Tracking

Update the Evolution Notes section:

```markdown
## Evolution Notes
- **Created**: [Original date] - Initial foundation
- **Updated**: [Current date] - Enhanced with codebase analysis
- **Patterns Discovered**: [List key patterns found]
- **Next Review**: [Suggest when to run update-rules again]
- **Decisions Needed**: [List areas where team consensus is still needed]
```

## Output Guidelines

1. **Be Specific**: Use actual file paths and code snippets from the codebase
2. **Show Examples**: Include real code examples, not generic ones
3. **Identify Gaps**: Point out inconsistencies or missing standards
4. **Suggest Improvements**: Recommend areas for standardization
5. **Preserve Evolution**: Maintain history of how rules developed

## Success Criteria

- Existing RULES.md is enhanced with concrete, actionable standards
- All "To Be Discovered" sections are populated with actual findings
- Code examples come from the real codebase
- Inconsistencies are identified and flagged for team decisions
- Evolution history is maintained