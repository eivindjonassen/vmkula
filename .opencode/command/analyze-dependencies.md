---
description: Technology stack and dependency analysis - delegates to @dependency-analysis agent
---

# Dependency Analysis Command (Delegation Wrapper)

This command automatically delegates to the specialized `@dependency-analysis` subagent for comprehensive technology stack auditing and vulnerability assessment.

## Usage

```bash
# Command syntax (auto-delegates)
/analyze-dependencies [target]

# Examples:
/analyze-dependencies .
/analyze-dependencies package.json
/analyze-dependencies "What is our current tech stack?"
```

## What Happens

1. Parses target input (directory, manifest file, or question)
2. Invokes @dependency-analysis subagent with:
   - Target scope
   - Project RULES.md (tech stack standards)
   - Relevant package manifests
3. Returns structured technology stack and dependency report

## Direct Agent Invocation

You can also invoke the agent directly:

```bash
@dependency-analysis .
```

## Output

Comprehensive dependency report covering:

### Evaluation Dimensions
- **Tech Stack Overview**: Package managers, frameworks, libraries.
- **Dependency Health**: Security vulnerabilities, outdated packages.
- **Architecture**: Inferred patterns from library choices.
- **Recommendations**: Upgrade paths and cleanup actions.

### Report Structure
- **Executive Summary**: Overall health and core stack.
- **Detailed Audit**: Tables of vulnerabilities and outdated packages.
- **Prioritized Plan**: Actionable steps for maintenance.

## Agent Configuration

- **Temperature**: 0.1 (deterministic dependency analysis)
- **Tools**: Bash (read-only commands), Webfetch (registry lookups)
- **Permissions**: Restrictive bash access for data collection
