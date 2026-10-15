# frr-route-reflector

An open-source FRRouting-based BGP Route Reflector CNF for Kubernetes.

## Status

**Experimental / lab-only; not production-ready.** Task 0001's Alpine FRR
container and deterministic Helm Chart were accepted through merged PR #6;
Issue #5 is closed. Native ARM64 G-2 evidence does not establish native AMD64
runtime acceptance. Historical AMD64 build/static evidence remains in closed,
unmerged PR #11; it is not part of accepted main. Native AMD64 execution and
G-3 Kubernetes deployment, routing, actual non-transit packet and lifecycle
acceptance remain NOT RUN / BLOCKED. No public image is authorized by this PR.

## Offline build and checks

Run the container build/tests on the authorized Linux container-development host.
Helm 3, Python 3 and PyYAML are required for tests; they are not runtime dependencies.

```sh
docker build -t frr-task0001:implementation container
helm lint charts/frr-route-reflector -f examples/documentation-values.json
helm template rr charts/frr-route-reflector -f examples/documentation-values.json
python3 tests/test_chart.py
python3 tests/test_container.py
python3 tests/test_container.py --missing-interface
python3 tests/test_container.py --drift
```

The example uses only RFC 5737 addresses, fake Workers and a non-existent image
digest. It is **not deployable or an accepted private lab binding**. Defaults
reject render until a complete input and explicit `lab-sysadmin` choice are given.
The drift test requires sudo for nsenter and changes only its disposable Docker
network namespace; it is never a command to run against Kubernetes or a Worker
network namespace. Tests use no external peers or host-directory mounts.

See [implementation binding](docs/implementation-binding.md),
[proposed runbook](docs/runbook.md) and [validation evidence](docs/tasks/0001-implementation-evidence.md).

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

## Implementation contract and acceptance boundary

The accepted baseline includes the [Implementation Contract](docs/implementation-contract.md), [ADR 0008](docs/adr/0008-config-ownership.md), [ADR 0009](docs/adr/0009-bare-pod-updates.md), and [Codex Task 0001](docs/tasks/0001-bootstrap-container-chart.md).

[Issue #5](https://github.com/si32288564/frr-route-reflector/issues/5) is closed;
[merged PR #6](https://github.com/si32288564/frr-route-reflector/pull/6) retains the
old STOP/diagnostic evidence alongside the accepted implementation. Accepted ADRs
[0010](docs/adr/0010-minimal-frr-runtime.md) and
[0011](docs/adr/0011-lab-frr-capability-profile.md) authorize the Alpine package
runtime and explicit lab-only profile. They do not authorize cluster policy
changes or production use. Existing Calico initializes namespace forwarding;
the entrypoint independently verifies it after all attachments.

## Development and governance

The project is developed publicly with GitHub as the Git source of truth. Architectural decisions and implementations are proposed through reviewable changes. The authoritative governance rules live in the ChatGPT Project; their synchronized repository copy will be maintained at [docs/PROJECT_GOVERNANCE.md](docs/PROJECT_GOVERNANCE.md).

## Usage and licensing

Original project scripts, Helm templates, tests and original documentation are
licensed under the [MIT License](LICENSE), with Owner-confirmed attribution
`Copyright (c) 2026 si32288564`. This grant does not relicense third-party files,
FRRouting, Alpine packages or dependencies bundled in container images.

See [third-party inventory and notice gaps](THIRD_PARTY_NOTICES.md) and
[publication preflight / source-delivery proposal](docs/publishing-preflight.md).
Public container-image distribution is BLOCKED pending corresponding source, complete notices,
security review and separate Owner authorization after this preparation PR is
reviewed and merged. A lab-only warning does not waive redistribution duties.
No internal employer-specific configurations or secrets belong in this repository.
