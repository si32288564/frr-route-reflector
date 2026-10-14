# Codex task 0001 — Bootstrap container and Helm render

> **Authority / state:** Task 0001 was authorized by merged PR #4 and Issue #5. It is **currently BLOCKED** by the FRR capability STOP in Draft PR #6. This branch proposes a bounded change to the container/base image selection; implementation cannot resume from this proposal until its own PR is reviewed and merged.  
> **Work location:** Owner's local clone. **Push:** GitHub working branch, Pull Request for Chat + Owner review.  
> **Architecture sources:** `docs/PROJECT_GOVERNANCE.md`, `docs/requirements.md`, `docs/architecture.md`, `docs/network-design.md`, `docs/acceptance-criteria.md`, `docs/implementation-contract.md`, ADR 0001–0010 (ADR 0010 becomes binding only after the design PR merges).

## Purpose

Build **one narrow, verifiable vertical slice**: a reusable FRR RR container and a Helm Chart that **deterministically renders** the accepted two-RR topology. Do not claim a finished CNF from an image build or template PASS.

## Inputs and invariants

- Use IPv4 OSPFv2 P2P on four VLAN /31 interfaces per RR, plus each RR's passive loopback /32.
- Use one shared BGP Cluster ID, distinct loopback/Router ID, four RR clients per RR, and no RR↔RR peering or NAD.
- Each RR is a **direct, fixed-placement Pod** on a distinct Worker, with `eth0` provided by Calico and four external Multus/VLAN CNI links. Total resources: 2 Pods, 2 per-RR FRR ConfigMaps, 8 NADs.
- Set RR OSPF permanent administrative max-metric, BGP no-rib, and a **real, Pod-local `net.ipv4.ip_forward=0` safety guard**.
- An RR must never forward packets; do not permit privileged/host-wide workarounds without Owner approval.

## Scope

1. Implement this project's own `container/` Dockerfile and start mechanism, **starting with an immutable-digest Alpine 3.24 base and an Alpine `v3.24/community` FRR package** (candidate `10.6.1-r0`; verify actual arch/revision). Do not base the runtime image on `quay.io/frrouting/frr`. Prefer distro-supplied FRR binaries and upstream process helpers; start `zebra`, `ospfd`, `bgpd` using integrated `frr.conf` and the distribution's required helpers. No FRR source fork or custom privilege patch. The single alternate candidate if Alpine fails is Debian Slim.
2. Implement `charts/frr-route-reflector/`: Chart metadata, values, schema, Pod + ConfigMap + NAD templates, deterministic names and interface references. No extra controller.
3. Implement safe handling of projected configuration and FRR runtime paths so startup consumes the rendered configuration. A Pod must reject incorrect number/type of external IFs before starting routing services.
4. Implement and document the namespace-local forwarding guard. In the disposable development environment evaluate the required capabilities for all routing daemons. **Do not add a shipped `CAP_SYS_ADMIN` or change cluster/host security policy without Owner's explicit security decision.** If the selected package cannot work under the approved runtime security profile, STOP with exact evidence and finite alternatives. A diagnostic test with `SYS_ADMIN` requires a scoped security review before execution, and must never be conflated with a release permission decision.
5. Implement template/schema/unit checks on cardinality, required identities, duplicate/missing links, /31 validity, VLAN bounds, unexpected route/NEXT_HOP policies, duplicate worker bindings and inclusion of private-looking sample values. Reject incomplete configuration.
6. Add `examples/` containing documentation-only addresses, clearly marked non-production, plus a minimal `README` for static rendering/build and explicit environment prerequisites.
7. Provide concise proposed, **not yet claimed valid**, operator steps for initial installation and safe one-sided replacement. Full recovery/rollback tests belong to integrated-lab acceptance.

## Validation required before Codex marks task complete

- `helm lint`, `helm template`, schema validation; inspect each of the 2 Pods, 2 ConfigMaps, and 8 NADs.
- Verify pairwise mapping from 2×4 links to the intended FRR `net1..net4` interfaces; test duplicate VLAN/IF/name/address, invalid CIDR/cardinality, and invalid or unsafe values **fail** rather than silently normalize.
- Validate FRR config syntax using a method actually supported by the chosen image/version. Include command and exact output, not hypothetical PASS.
- Show Alpine base image digest, FRR package version/revision and provenance, resolved dependencies, final image digest, installed file inventory, size and available SBOM/scan evidence. Image build itself only counts as PASS if executed. Compare Debian Slim only if the Alpine candidate fails a defined gate.
- Where the cluster/lab is available, capture observed netns forwarding state, FRR daemon startup, interfaces and neighbor state. Clearly report **NOT RUN** for unavailable runtime checks.
- No Test-to-Test transit, CNI attach, OSPF Full or BGP Established claim without actual lab evidence.

## Explicit STOP conditions

- Any new Architecture choice needed beyond the accepted implementation contract.
- The chosen FRR package requires a capability not approved for the **release/runtime manifest**, such as `SYS_ADMIN`, or any `privileged`, host-network, host-sysctl, or host-mount escalation. Record why the daemon requests it and return to Chat/Owner; do not turn a disposable diagnostic into permanent permission.
- Loopback identity cannot be installed reliably or conflicts with another owner.
- The container becomes routable/ready while Pod-local forwarding is not confirmed disabled.
- Helm update/replacement appears to depend on implicit auto-recreation of bare Pods.
- A test result or config requires disclosing non-public company data to GitHub.

When STOP occurs, submit **a minimal reproducible fact, affected requirement/invariant, candidate finite remedy, and whether it blocks this task**. Do not create a new general-purpose state machine/controller.

## Existing STOP evidence and next bounded action

Draft [PR #6](https://github.com/si32288564/frr-route-reflector/pull/6) holds the original FRR 10.3.1 capability reproduction. **Preserve it as valid evidence**, not as a fully implemented task.

After Owner acceptance/merge of [ADR 0010](../adr/0010-minimal-frr-runtime.md), examine the pinned Alpine-based runtime candidate **before resuming all Chart work**:

1. Capture Alpine `3.24` base digest, Alpine FRR package version/revision, supported architecture and dependency manifest.
2. Test the FRR daemons' startup using the permitted limited capability set and the same strict nontransit forwarding guard. Log exact failures, user, capabilities and seccomp/admission conditions.
3. If the Alpine candidate cannot start/function within approved permissions, evaluate **one pinned Debian Slim + FRR package** candidate; no random tag sweeps.
4. If `SYS_ADMIN` remains necessary, provide the evidence and security tradeoff for Owner approval. Stop before adopting any enlarged shipped permission, patched/disabled FRR privilege management or broad privileged runtime.
5. When a base/runtime candidate meets the agreed gate, implement the original fixed-scope container/Helm slice and tests, rebase/update the Draft PR safely without rewriting accepted `main`.

Do not claim that an Alpine package install yields only three daemon binaries or that a smaller image is automatically safer. Alpine `community` packages have a **different security maintenance window** from the Alpine `main` branch.

## Pull Request format

- Link the accepted contract and this task; list precisely changed files.
- Provide an evidence table with **PASS / FAIL / NOT RUN / BLOCKED**, runtime/tool versions, and the commands actually executed.
- Show sample rendered object counts and key invariants, not a full unredacted employer network dump.
- Do not merge to `main`: await Chat's architecture review and Owner acceptance.

## Done means

A deterministic, reviewable FRR container + two-RR Helm render exists with validated safety checks and complete negative tests **to the level actually executed**. It does *not* mean the CNF has already passed integrated network or failure tests.
