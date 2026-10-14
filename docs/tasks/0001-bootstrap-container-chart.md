# Codex task 0001 — Bootstrap container and Helm render

> **Status:** Proposed task / **NOT authorized for execution** until the Implementation Contract PR is approved and merged to `main`.  
> **Work location:** Owner's local clone. **Push:** GitHub working branch, Pull Request for Chat + Owner review.  
> **Architecture sources:** `docs/PROJECT_GOVERNANCE.md`, `docs/requirements.md`, `docs/architecture.md`, `docs/network-design.md`, `docs/acceptance-criteria.md`, `docs/implementation-contract.md`, ADR 0001–0009.

## Purpose

Build **one narrow, verifiable vertical slice**: a reusable FRR RR container and a Helm Chart that **deterministically renders** the accepted two-RR topology. Do not claim a finished CNF from an image build or template PASS.

## Inputs and invariants

- Use IPv4 OSPFv2 P2P on four VLAN /31 interfaces per RR, plus each RR's passive loopback /32.
- Use one shared BGP Cluster ID, distinct loopback/Router ID, four RR clients per RR, and no RR↔RR peering or NAD.
- Each RR is a **direct, fixed-placement Pod** on a distinct Worker, with `eth0` provided by Calico and four external Multus/VLAN CNI links. Total resources: 2 Pods, 2 per-RR FRR ConfigMaps, 8 NADs.
- Set RR OSPF permanent administrative max-metric, BGP no-rib, and a **real, Pod-local `net.ipv4.ip_forward=0` safety guard**.
- An RR must never forward packets; do not permit privileged/host-wide workarounds without Owner approval.

## Scope

1. Implement `container/` Dockerfile and start mechanism using a **pinned and documented FRR version**. Start `zebra`, `ospfd`, `bgpd` with the integrated `frr.conf` and only necessary standard FRR helpers/supervisor. Prefer upstream-supported primitives.
2. Implement `charts/frr-route-reflector/`: Chart metadata, values, schema, Pod + ConfigMap + NAD templates, deterministic names and interface references. No extra controller.
3. Implement safe handling of projected configuration and FRR runtime paths so startup consumes the rendered configuration. A Pod must reject incorrect number/type of external IFs before starting routing services.
4. Implement and document an explicit namespace-local forwarding guard. If the selected Kubernetes Pod security context cannot enforce it, **STOP with exact runtime/permission evidence**; do not silently downgrade the hard invariant.
5. Implement template/schema/unit checks on cardinality, required identities, duplicate/missing links, /31 validity, VLAN bounds, unexpected route/NEXT_HOP policies, duplicate worker bindings and inclusion of private-looking sample values. Reject incomplete configuration.
6. Add `examples/` containing documentation-only addresses, clearly marked non-production, plus a minimal `README` for static rendering/build and explicit environment prerequisites.
7. Provide concise proposed, **not yet claimed valid**, operator steps for initial installation and safe one-sided replacement. Full recovery/rollback tests belong to integrated-lab acceptance.

## Validation required before Codex marks task complete

- `helm lint`, `helm template`, schema validation; inspect each of the 2 Pods, 2 ConfigMaps, and 8 NADs.
- Verify pairwise mapping from 2×4 links to the intended FRR `net1..net4` interfaces; test duplicate VLAN/IF/name/address, invalid CIDR/cardinality, and invalid or unsafe values **fail** rather than silently normalize.
- Validate FRR config syntax using a method actually supported by the chosen image/version. Include command and exact output, not hypothetical PASS.
- Show the image build recipe and digest/version used. Image build itself only counts as PASS if executed.
- Where the cluster/lab is available, capture observed netns forwarding state, FRR daemon startup, interfaces and neighbor state. Clearly report **NOT RUN** for unavailable runtime checks.
- No Test-to-Test transit, CNI attach, OSPF Full or BGP Established claim without actual lab evidence.

## Explicit STOP conditions

- Any new Architecture choice needed beyond the accepted implementation contract.
- The FRR image requires broad privilege (e.g. `privileged: true` or `SYS_ADMIN`) or host-network/sysctl mutation not already approved.
- Loopback identity cannot be installed reliably or conflicts with another owner.
- The container becomes routable/ready while Pod-local forwarding is not confirmed disabled.
- Helm update/replacement appears to depend on implicit auto-recreation of bare Pods.
- A test result or config requires disclosing non-public company data to GitHub.

When STOP occurs, submit **a minimal reproducible fact, affected requirement/invariant, candidate finite remedy, and whether it blocks this task**. Do not create a new general-purpose state machine/controller.

## Pull Request format

- Link the accepted contract and this task; list precisely changed files.
- Provide an evidence table with **PASS / FAIL / NOT RUN / BLOCKED**, runtime/tool versions, and the commands actually executed.
- Show sample rendered object counts and key invariants, not a full unredacted employer network dump.
- Do not merge to `main`: await Chat's architecture review and Owner acceptance.

## Done means

A deterministic, reviewable FRR container + two-RR Helm render exists with validated safety checks and complete negative tests **to the level actually executed**. It does *not* mean the CNF has already passed integrated network or failure tests.
