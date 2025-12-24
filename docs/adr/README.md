# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for this project.

## What is an ADR?

An Architecture Decision Record (ADR) is a document that captures an important architectural decision made along with its context and consequences.

## ADR Template

Use the following template for new ADRs:

```markdown
# [NUMBER]. [TITLE]

Date: YYYY-MM-DD

## Status

[Proposed | Accepted | Deprecated | Superseded]

## Context

What is the issue that we're seeing that is motivating this decision or change?

## Decision

What is the change that we're proposing and/or doing?

## Consequences

What becomes easier or more difficult to do because of this change?

### Positive Consequences
- [e.g., improvement of quality attribute satisfaction, follows architectural principles]

### Negative Consequences  
- [e.g., compromising quality attribute, conflicts with architectural principles]

## Alternatives Considered

What other options were evaluated?

## References

- [Link to related documentation]
- [Link to discussions]
```

## Index of ADRs

- [ADR-001: Certificate-Based Authentication with MSAL Python](./001-certificate-based-authentication.md)
- [ADR-002: Repository Pattern for Data Access](./002-repository-pattern.md)
- [ADR-003: FastAPI Framework Selection](./003-fastapi-framework.md)
- [ADR-004: Monorepo Structure](./004-monorepo-structure.md)
