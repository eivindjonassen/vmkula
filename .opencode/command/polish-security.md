---
description: Security review - delegates to @security-review agent
---

# Security Review Command (Delegation Wrapper)

This command automatically delegates to the specialized `@security-review` subagent for comprehensive security analysis and vulnerability assessment.

## Usage

```bash
# Command syntax (auto-delegates)
/polish-security [target]

# Examples:
/polish-security src/auth/login.ts
/polish-security src/api/
/polish-security "How should we handle CORS?"
```

## What Happens

1. Parses target input (file path, directory, or description)
2. Invokes @security-review subagent with:
   - Target files/description
   - Project RULES.md (security standards)
   - Relevant specs (if available)
3. Returns structured security report

## Direct Agent Invocation

You can also invoke the agent directly:

```bash
@security-review src/auth/login.ts
```

## Output

Comprehensive security report covering:

### Evaluation Dimensions
- **Vulnerability Analysis**: OWASP Top 10, Injection, XSS, etc.
- **Data Handling**: Input validation, sanitization, PII protection.
- **Architecture**: Least privilege, defense in depth.
- **Secrets Management**: Hardcoded credentials, environment variables.

### Report Structure
Severity-rated findings (Critical/High/Medium/Low) with:
- Specific location and impact
- Actionable recommendations
- Code examples (before/after)
- Remediation plan

## Agent Configuration

- **Temperature**: 0.1 (deterministic security analysis)
- **Tools**: Read-only (no code modifications)
- **Webfetch**: Enabled (can reference CVE databases, OWASP)
