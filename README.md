# frr-route-reflector

An open-source FRRouting-based BGP Route Reflector CNF for Kubernetes.

## Status

**Task 0001 implementation under review in Draft PR #6.** A project-owned Alpine
FRR container and deterministic Helm Chart are available in the working branch.
Kubernetes deployment, routing and packet/lifecycle acceptance remain NOT RUN.

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
Each RR's BGP Cluster ID is generated from its own `routers[].loopback` IPv4
without `/32`; do not supply `cluster.clusterId` or `routers[].clusterId`.
Legacy shared-ID values are rejected rather than ignored. See
[ADR 0012](docs/adr/0012-cluster-id-from-rr-loopback.md) for the breaking input
change and controlled migration boundary. Historical shared-ID runtime results
do not prove live behavior for this policy.
The drift test requires sudo for nsenter and changes only its disposable Docker
network namespace; it is never a command to run against Kubernetes or a Worker
network namespace. Tests use no external peers or host-directory mounts.

See [implementation binding](docs/implementation-binding.md),
[proposed runbook](docs/runbook.md) and [validation evidence](docs/tasks/0001-implementation-evidence.md).

## Scope

### Core OSPF with multiple iBGP peers

Select `topology: core` for one `net1` /31 VLAN link from each RR to core
(two Pods, two ConfigMaps, two NADs). OSPF is P2P on that link and advertises the
RR loopback passively; core must provide reachability to/from remote loopbacks.
Each router's independent `neighbors` list may contain multiple IPv4 iBGP peers:

```yaml
# Excerpt under routers[]; complete documentation fixture linked below.
neighbors:
  - address: 192.0.2.11
    routeReflectorClient: true
  - address: 192.0.2.12
    routeReflectorClient: true
  - address: 192.0.2.2
    routeReflectorClient: false  # Optional opposite RR, normal iBGP peer.
```

Addresses above are documentation-only. All remote-as values use
`cluster.bgpAsn` and update-source is the local RR loopback. `clients` must be
empty in this mode; no duplicate peer source, per-peer eBGP ASN or raw FRR text.
At least one RR Client is required; duplicate/self/RR-as-Client peers are rejected.
Peer count does not change the one core attachment or its OSPF configuration.
Use [the complete core fixture](examples/core-documentation-values.json) as a
shape example, **not live IPAM**. Default `placement: distinct-workers` preserves
fixed separate Workers. Explicit `placement: single-worker` is available only
for core-mode home development, not Worker redundancy.

Without this opt-in the original four-direct-Client topology is unchanged.
Core mode requires the updated one-interface-capable entrypoint image; old
four-interface images will refuse startup. Neither the Chart nor image configures
core/Client devices or host networking. See [ADR 0013](docs/adr/0013-core-ospf-independent-ibgp-neighbors.md).

On a proxy-only build host, pass its **existing** proxy environment through
Docker's predefined build arguments; do not add proxy URLs/credentials to the
Dockerfile, values or Git. For example, when Docker requires sudo:

```sh
sudo --preserve-env=HTTP_PROXY,HTTPS_PROXY,NO_PROXY,http_proxy,https_proxy,no_proxy \
  docker build --build-arg HTTP_PROXY --build-arg HTTPS_PROXY --build-arg NO_PROXY \
  --build-arg http_proxy --build-arg https_proxy --build-arg no_proxy \
  -t frr-core:implementation container
```

Both ARM64 and AMD64 are intended targets. An ARM64 build or syntax check is not
AMD64 qualification. Cross-building the package-install stage on an ARM64 host
requires a working AMD64 execution backend/emulator; none is silently installed.

```sh
python3 tests/test_core_chart.py
python3 tests/test_entrypoint_inventory.py
helm lint charts/frr-route-reflector -f examples/core-documentation-values.json
helm template rr charts/frr-route-reflector -f examples/core-documentation-values.json
```

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

[Issue #5](https://github.com/si32288564/frr-route-reflector/issues/5) is active;
[Draft PR #6](https://github.com/si32288564/frr-route-reflector/pull/6) retains the
old STOP/diagnostic evidence alongside implementation. Accepted ADRs
[0010](docs/adr/0010-minimal-frr-runtime.md) and
[0011](docs/adr/0011-lab-frr-capability-profile.md) authorize the Alpine package
runtime and explicit lab-only profile. They do not authorize cluster policy
changes or production use. Existing Calico initializes namespace forwarding;
the entrypoint independently verifies it after all attachments.

## Development and governance

The project is developed publicly with GitHub as the Git source of truth. Architectural decisions and implementations are proposed through reviewable changes. The authoritative governance rules live in the ChatGPT Project; their synchronized repository copy will be maintained at [docs/PROJECT_GOVERNANCE.md](docs/PROJECT_GOVERNANCE.md).

## Usage and licensing

This repository is not yet released for production use. Distribution terms and the OSS license are pending an explicit project decision. No internal employer-specific configurations or secrets belong in this public repository.
