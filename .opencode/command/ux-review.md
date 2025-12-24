---
description: UX review - delegates to @ux-review agent
---

# UX Review Command (Delegation Wrapper)

This command automatically delegates to the specialized `@ux-review` subagent for comprehensive user experience evaluation.

## Usage

```bash
# Command syntax (auto-delegates)
/ux-review [target]

# Examples:
/ux-review src/components/LoginForm.tsx
/ux-review src/pages/checkout/
/ux-review "Should I use tabs or accordion?"
```

## What Happens

1. Parses target input (file path, directory, or description)
2. Invokes @ux-review subagent with:
   - Target files/description
   - Project RULES.md (design patterns, accessibility)
   - Relevant specs (if available)
3. Returns structured UX report

## Direct Agent Invocation

You can also invoke the agent directly:

```bash
@ux-review src/components/Button.tsx
```

## Output

Comprehensive UX report covering:

### Evaluation Dimensions
- **Core UX Laws**: Fitts's, Hick's, Jakob's, Miller's
- **Design Principles**: Consistency, Affordances, Control & Freedom
- **Accessibility**: WCAG 2.1 AA/AAA compliance
- **Mobile & Responsive**: Touch targets, thumb zones, viewport adaptation
- **Conversion Optimization**: Funnel analysis, friction reduction
- **Information Architecture**: Navigation, content hierarchy
- **Visual Design**: Typography, spacing, color, imagery
- **Performance**: Loading states, perceived speed

### Report Structure
Severity-rated findings (Critical/High/Medium/Low) with:
- Specific location and description
- User impact analysis
- Actionable recommendations
- Code examples (before/after)
- Integration with Bifrost workflow (task creation, RULES.md updates)

## Agent Configuration

- **Temperature**: 0.2 (balanced analysis with creative suggestions)
- **Tools**: Read-only (no code modifications)
- **Webfetch**: Enabled (can reference WCAG guidelines, design patterns)
- **Model**: Inherits from parent agent (flexible for fast vs comprehensive reviews)
