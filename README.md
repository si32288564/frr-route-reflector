# frr-route-reflector

An open-source FRRouting-based BGP Route Reflector CNF for Kubernetes.

## Status

**Design / pre-implementation.** No container image, Helm chart, or validated deployment is available yet.

## Scope

The initial target is an IPv4-only Route Reflector implemented with FRRouting, deployed as Kubernetes Pods and connected to external networks through Multus. Detailed, accepted requirements and architecture will be maintained under `docs/`; implementation must not infer architecture from this introduction.

## Design authorities

The following documents record the accepted architecture on `main`. Changes in unmerged PRs remain proposals:

- [Requirements](docs/requirements.md)
- [Architecture](docs/architecture.md)
- [Network design](docs/network-design.md)
- [Acceptance criteria](docs/acceptance-criteria.md)
- Architecture Decision Records: [ADR 0001](docs/adr/0001-two-rr-one-cluster.md), [ADR 0002](docs/adr/0002-fixed-bare-pods.md), [ADR 0003](docs/adr/0003-multus-vlan-cni.md), [ADR 0004](docs/adr/0004-no-rr-ip-transit.md), [ADR 0005](docs/adr/0005-client-transit-broadcast.md), [ADR 0006](docs/adr/0006-client-next-hop-self.md), [ADR 0007](docs/adr/0007-rr-nontransit-enforcement.md)

The design documents do **not** establish that a CNF has been built, deployed, or tested.

## Implementation contract and current STOP

The accepted baseline includes the [Implementation Contract](docs/implementation-contract.md), [ADR 0008](docs/adr/0008-config-ownership.md), [ADR 0009](docs/adr/0009-bare-pod-updates.md), and [Codex Task 0001](docs/tasks/0001-bootstrap-container-chart.md).

[Issue #5](https://github.com/si32288564/frr-route-reflector/issues/5) is the active task; [Draft PR #6](https://github.com/si32288564/frr-route-reflector/pull/6) records the FRR 10.3.1 `CAP_SYS_ADMIN` startup STOP, **not a finished implementation**. The proposed [ADR 0010](docs/adr/0010-minimal-frr-runtime.md) selects a **dedicated Alpine 3.24 + FRR package** runtime as the first candidate. This only becomes accepted after its design PR is merged; it does not automatically grant any expanded Linux capability.

## Development and governance

The project is developed publicly with GitHub as the Git source of truth. Architectural decisions and implementations are proposed through reviewable changes. The authoritative governance rules live in the ChatGPT Project; their synchronized repository copy will be maintained at [docs/PROJECT_GOVERNANCE.md](docs/PROJECT_GOVERNANCE.md).

## Usage and licensing

This repository is not yet released for production use. Distribution terms and the OSS license are pending an explicit project decision. No internal employer-specific configurations or secrets belong in this public repository.
