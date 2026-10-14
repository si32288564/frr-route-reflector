# Agent instructions

Before editing this repository, read [docs/PROJECT_GOVERNANCE.md](docs/PROJECT_GOVERNANCE.md) in full. This file is a synchronized copy of the governance document maintained in the ChatGPT Project; it is not an independent authority.

## Responsibilities

- The Owner makes final product, architecture-approval, release, and publication decisions.
- ChatGPT Chat is the PM / Architecture Owner; it defines requirements, architectural boundaries, invariants, and acceptance criteria.
- Codex implements and validates accepted, task-scoped specifications in the Owner's local development/test environment. It must not invent or unilaterally revise higher-level architecture.

## Working rules

1. Read accepted requirements, architecture, ADRs, and task acceptance criteria on `main` before beginning implementation.
2. Work on a branch; push changes and create a pull request with scope, test evidence, and known limitations. Do not directly push ordinary changes to `main`.
3. Stop and report reproducible evidence when requirements conflict, the accepted architecture is insufficient, or the requested change affects security, network roles, lifecycle, or public disclosure boundaries. Do not hide inconsistencies with special cases.
4. Treat runtime observations and tests as evidence, not as a replacement for accepted architecture. Never claim to have executed tests not actually run.
5. Do not commit internal company configuration, secrets, production identifiers, or non-public logs to this public repository.
6. Do not add permanent abstractions or framework machinery solely for hypothetical future requirements.

If this file conflicts with the ChatGPT Project governance or the repository copy of it, stop and request reconciliation; do not silently choose a new authority.
