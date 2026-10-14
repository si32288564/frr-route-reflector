# Implementation contract — FRR CNF and Helm Chart

> **Status:** Proposal on `design/implementation-contract`; not authoritative until Owner approval and merge to `main`.  
> Governing sources: [Governance](PROJECT_GOVERNANCE.md), [requirements](requirements.md), [architecture](architecture.md), [network design](network-design.md), [acceptance criteria](acceptance-criteria.md), and ADRs 0001–0007. This contract **binds their implementation projection**, not a new routing architecture.

## 1. Explicit implementation boundary

Implement **exactly two logical RR CNFs** in the initial lab through **one Helm release**. The Chart owns:
- 2 directly managed `v1/Pod` resources (one pinned to each Worker).
- 8 `NetworkAttachmentDefinition` resources (4 independent VLAN CNI links per RR).
- 2 per-RR `ConfigMap` objects containing generated FRR boot configuration.
- Schema/semantic validation, test fixtures, and an operator-facing install/update/recovery procedure.

It does **not** own the 4 external RR clients, 4 eBGP Test peers, Client Transit VLAN, upstream physical switches, Worker NIC setup, or Multus/CNI installation.

No `Deployment`, `StatefulSet`, new controller/operator, RR↔RR peering, hostNetwork, SR-IOV, macvlan or ipvlan belongs to the initial implementation.

## 2. Single source and deterministic projections

A structured Helm values input is the **configuration SSOT** for the RR release. Do **not** ingest arbitrary external FRR config as a second independent source. One `values.yaml` schema maps to exactly one deterministic set of Kubernetes objects and FRR text.

A minimal semantic model is:

| Object | Required properties | Cardinality |
|---|---|---|
| cluster | IPv4 iBGP ASN, Cluster ID, OSPF area | 1 |
| RR | stable name, Router ID, loopback /32, Node selector, physical master, image selection | 2, distinct |
| Client | stable name, BGP neighbor loopback /32, iBGP ASN inherited from cluster | 4, distinct |
| RR↔Client attachment | RR ref, Client ref, Pod interface name, VLAN ID, local IPv4 /31, OSPF area ref | 8, complete 2×4 product |
| eBGP/Test/Client Transit | not RR Chart resources; documented external requirements | outside Helm SSOT |

Example **shape** only, not an accepted lab addressing plan:

```yaml
cluster:
  bgpAsn: 64512
  clusterId: 192.0.2.254
  ospfArea: 0.0.0.0

clients:
  - name: client1
    loopback: 192.0.2.11/32
  # ... three more

routers:
  - name: rr01
    routerId: 192.0.2.1
    loopback: 192.0.2.1/32
    nodeSelector:
      cnf.example.org/rr-slot: rr01
    vlanMaster: <worker-external-interface>
    links:
      - client: client1
        interface: net1
        vlanId: 1101
        localAddress: 198.51.100.0/31
      # ... three more
  # ... rr02
```

The above is a **partial illustrative input**, not directly deployable and not employer-specific. The toolchain must reject missing/incomplete input. An example may supply dummy values (RFC 5737 documentation ranges) but **must not silently become the production default**.

Required validation:
- Exactly 2 distinct RR identities and fixed, distinguishable Worker placement constraints; 4 distinct Client identities.
- Exactly one RR↔Client link per pair, no missing or duplicated pair.
- For each Worker, no duplicate `(physical master, VLAN ID)`; in this initial lab the total 8 links are distinct VLAN segments.
- Unique Pod-facing secondary interface names per RR, no collision with `eth0` or `lo`; all interfaces have syntactically valid names and non-overlapping IPv4 /31 links.
- /32 loopback addresses do not collide; RR Router IDs distinct; Cluster ID shared; no host-network routing identifiers tied to ephemeral Calico primary Pod IP.
- VLAN IDs in 1–4094, /31 addresses must actually be /31, and the external client endpoint address must be the opposite member of the pair. Exact remote endpoint values belong in lab binding; validate their declared relation when provided.
- The FRR configuration and Multus annotations must refer to **the same** interface identifiers, VLANs and loopback/BGP identities; no arbitrary FRR commands inserted through values in v1.
- Fail template/schema validation on invalid input. JSON Schema alone cannot prove every cross-object uniqueness constraint; use finite Helm template checks and/or deterministic offline rendering tests. Never silently drop an invalid link.

## 3. FRR process contract

- Use a **version-pinned FRRouting** distribution/image; no floating `latest` or unreviewed external build inputs in a published release. Image digest/provenance is established during the implementation task.
- Use FRR's **integrated** `/etc/frr/frr.conf` as the single startup configuration, generated from Helm values. Enable routing roles `zebra`, `ospfd`, and `bgpd` only, plus whichever FRR **configuration/process supervisor** services the chosen distribution requires (for example `watchfrr` / `mgmtd`). Do not invent a parallel routing daemon manager.
- All daemon processes share **the RR Pod network namespace**. No per-peer child Pods and no node-wide FRR.
- The container startup path must materialize the projected configuration in a **writable, Pod-private runtime directory** if FRR tooling requires mutable configuration/pid/socket files. A read-only ConfigMap file must not be overwritten. The canonical input remains Helm values; runtime files are derived.
- Start only after Multus has attached four interfaces, the RR's stable loopback /32 is installed in its Pod namespace, and the **non-forwarding safety gate** has been established/verified. The exact loopback creation primitive (FRR `interface lo` or idempotent entrypoint setup) must be proven against the selected FRR and container runtime; only one component may own the address.
- BGP IPv4-unicast peers use the four Client loopbacks and `update-source` bound to the RR loopback; each peer is `route-reflector-client`. Both RR ConfigMaps use the same Cluster ID. No RR↔RR neighbor, IPv6 BGP, OSPFv3, or test-prefix redistribution into OSPF.
- OSPFv2 is P2P on each of the four Multus link interfaces and advertises the RR loopback /32 as a **passive loopback**. Apply permanent `max-metric router-lsa administrative`. Maintain IGP reachability needed for BGP NEXT_HOP tracking.
- Apply `bgp no-rib` to avoid pushing BGP service routes into Zebra/kernel FIB. Verify that it still supports client route reflection; if not, STOP with evidence. `bgp no-rib` is *not* the IP forwarding control.

See [ADR 0008](adr/0008-config-ownership.md) for the configuration-authority decision.

## 4. Kubernetes / NAD object contract

Every RR Pod:
- Is `kind: Pod`, explicitly pinned using a distinct **Node selector** that matches exactly one intended Worker in the lab. Do not silently fall back to another Worker if the labeled one disappears.
- Has `restartPolicy: Always` for container-process crashes but **no** application controller recreating a deleted/evicted Pod.
- Has one Calico primary `eth0` reserved for ordinary Kubernetes control-plane management (not the FRR's external BGP/OSPF path), and exactly four Multus secondary interfaces named by the release values.
- Sets `hostNetwork: false`, disables automatic service-account token mounting, uses dedicated ConfigMap/emptyDir volumes, and does not require a Node hostPath for FRR state.
- Requests only the minimum Linux capabilities and Pod privileges proven necessary for FRR, packet sockets, stable loopback and namespace-local safety gate. **Privileged mode and `SYS_ADMIN` are not the default.** If the chosen FRR image/cluster constraints require wider privileges, stop and present a security decision to Owner.
- Must guard against client-facing operation if `net.ipv4.ip_forward` is not verified as `0` in the **Pod netns**. Do not edit Worker host sysctls or weaken kubelet security policy as a hidden workaround.

Every NAD:
- References CNI `type: vlan`, the validated worker `master`, a unique `vlanId`, and static IPAM with the appropriate RR-side /31.
- Is created by the Helm release and referenced in the matching Pod's `k8s.v1.cni.cncf.io/networks` annotation with deterministic interface names.
- Does not set a gateway/default route via the RR-to-client /31 links. Loopback reachability is learned by OSPF, not an IPAM default route.
- Has a lifecycle tied to its RR release, with explicit deletion/cleanup checks for stale VLAN interfaces after Pod removal.

The Worker physical NIC and external switch trunk **must already be configured**; the Chart must not mutate them.

## 5. Safety, probes, and runtime observability

**Mandatory non-transit invariant:** Pod `net.ipv4.ip_forward = 0`. A startup precondition checks and enforces this *inside the Pod namespace*, and recurring verification detects drift. Do not treat Pod readiness alone as an enforcement mechanism: a readiness probe that fails does not stop a BGP daemon or prevent forwarding. A violation must stop routing services/terminate the container **fail-closed**.

Probes:
- Startup: FRR startup/config loaded, namespace forwarding guard in force, expected interfaces/loopback present.
- Liveness: supervisor/daemon health sufficient to restart a genuinely broken container; do **not** restart an otherwise healthy RR because a client, switch or OSPF neighbor is temporarily unavailable.
- Readiness: FRR operating state plus safety check; **do not require all four BGP peers Established** as a readiness prerequisite. Neighbor liveness is a separate status/metric.
- Security/probe helpers do not require an always-running custom controller.

Expose diagnostic commands or a minimal operator runbook to inspect effective `frr.conf`, 4 OSPF adjacencies, 4 BGP neighbor states, BGP next-hop information, ip forwarding value, net1–4 addresses, and CNI attachments. Logs must not publish employer-specific addresses/identifiers.

## 6. Update, restart, recovery, and rollback contract

**No implicit in-place mutable config workflow.** Helm values/configmap modification does not itself restart an existing Bare Pod or apply a new FRR running configuration. A Pod annotation checksum is audit metadata, **not a replacement controller**.

- Treat the accepted desired state as a Helm-rendered **immutable boot snapshot** per RR instance. A change in effective boot configuration requires **an explicit Pod replacement/restart procedure**, carried out one RR at a time after verifying the other RR remains available.
- The operation must clearly distinguish: image/config change, Pod deletion, Worker loss, CNI attachment failure, and Helm release removal. Do not invent a StatefulSet-like rolling update.
- Never assume `helm upgrade` can mutate all bare-Pod fields; immutable changes can fail and replacement must be controlled. Until the runbook is tested, **automatic Helm-only rolling update is out of scope**.
- Do not allow overlapping old/new incarnations of the same logical RR identity. For Pod recreation, ensure the former instance has terminated and its interface/VLAN resources are released before bringing the new one into service. No new fencing controller is authorized.
- For a Worker outage, **do not** recreate its RR on the other Worker. Recovery is an operator-controlled action only after the bound Worker/network resources are restored.
- Define rollback as restoring the previous accepted image/config snapshot and performing the same deliberate, sequential replacement. Rollback success must be observed, not assumed.
- Test deletion, container restart, reattachment and recoverability in the lab **before** claiming the runbook ready.

See [ADR 0009](adr/0009-bare-pod-updates.md).

## 7. Scope of first Codex work

The first task is not a complete network-validated CNF. Implement a **minimum coherent, statically verifiable vertical slice**:
- Reproducible FRR container skeleton and integrated FRR config startup path.
- Helm chart rendering two independently addressed bare Pods, two FRR ConfigMaps, eight NADs and deterministic annotations.
- Schema and targeted failure tests for invalid cardinality, duplicate VLAN/interface/address and invalid IP combinations.
- Non-transit configuration and **explicitly isolated runtime enforcement** with a fail-closed startup path.
- Clear environment prerequisites, sample values with documentation-only addresses and exact `NOT RUN` statements for lab-dependent behavior.

Out of first task: Client Transit provisioning, Test peers, public image release, timing/performance tuning, implementation of a new controller, and **claims of actual OSPF/BGP establishment or end-to-end data-plane transit tests**. A human and Chat must review the static implementation before integrated-lab work.

The proposed Codex handoff is [tasks/0001-bootstrap-container-chart.md](tasks/0001-bootstrap-container-chart.md), accepted only after this PR's merge.

## 8. Owner decisions and evidence needed

| Item | Owner decision now? | Reason |
|---|---|---|
| Helm values → generated per-RR FRR config; fixed bare-Pod lifecycle | **Yes: by approving this contract PR** | Architecture interface and operational semantics |
| Runtime permissions to enforce namespace forwarding gate | **Only if minimal-capability approach fails** | Security boundary; collect test evidence first |
| Actual NIC names, VLAN IDs, CIDRs, ASN, OSPF area | **Not required for public code skeleton** | Provide by local binding; never commit internal details |
| OSS LICENSE choice (e.g. Apache-2.0 or MIT) | **Before public distribution/release** | Legal/copyright/redistribution rights |
| Docker Hub vs GHCR; public chart OCI endpoint | **Before publishing release artifacts** | Independent release policy, not needed for local build |
| Automatic failover, HA controller, live reconfiguration | **No** | Outside initial accepted Architecture |

## References (implementation constraints; not test evidence)

- [FRRouting integrated configuration](https://docs.frrouting.org/en/latest/basic.html)
- [FRRouting BGP no-rib and RR](https://docs.frrouting.org/en/latest/bgp.html)
- [FRRouting OSPF max-metric](https://docs.frrouting.org/en/latest/ospfd.html)
- [CNI VLAN plugin](https://www.cni.dev/plugins/current/main/vlan/)
- [Kubernetes safe/unsafe sysctls](https://kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster/)
- [Kubernetes probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)
