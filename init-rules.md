# Project Constitution Generation

## Execution Flow
1.  Greet the user and explain that you will ask a series of questions to generate a `RULES.md` file for their project.
2.  Ask each question from the "Interview Questions" section below, one by one.
3.  For each question, provide the example answers to guide the user.
4.  Based on the user's answers, construct a `RULES.md` file.
5.  Use the structure from the "Output Structure" section below, filling in the blanks with the user's responses.
6.  Present the final `RULES.md` to the user for their review and approval.

---

## Interview Questions

1.  **Core Philosophy**: What are the main guiding principles for this project? (e.g., "Domain-First Design", "Move Fast and Break Things", "Strict Type Safety").
2.  **Project Structure**: How would you describe the project's structure? (e.g., "Monorepo with multiple apps", "Standard Web App with frontend/ and backend/ folders", "Standalone Service").
3.  **Primary Technologies**: What are the primary languages, frameworks, and databases for this project? (e.g., "TypeScript, React, Node.js, PostgreSQL").
4.  **Hosting Platform**: Where will this application be hosted? (e.g., "Google Cloud", "AWS", "Azure", "Firebase", "Vercel", "Netlify").
5.  **API Design**: What is the primary API style? (e.g., "RESTful with OpenAPI", "gRPC with Protobuf", "GraphQL").
6.  **Testing Strategy**: What is your testing philosophy? (e.g., "TDD is mandatory", "E2E tests for critical paths", "Unit tests for all services").
7.  **Dependency Management**: What package manager do you use? (e.g., "npm", "yarn", "pip", "maven").

---

## Output Structure (for the generated RULES.md)

```markdown
# [Project Name] Development Rules

## 1. Guiding Principles

- [Answer from Question 1]

## 2. Core Architecture

### Project Structure

- [Answer from Question 2]

### Primary Technologies

- **Language/Framework**: [Answer from Question 3]
- **Database**: [Answer from Question 3]

### Hosting Platform

- [Answer from Question 4]

### API Design

- [Answer from Question 5]

## 3. Development Practices

### Testing

- [Answer from Question 6]

### Dependency Management

- [Answer from Question 7]
```
