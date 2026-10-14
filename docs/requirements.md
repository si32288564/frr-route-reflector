# Requirements — frr-route-reflector

> **Authority status:** This content is a proposal on a non-merged PR branch. It becomes accepted requirements only when reviewed and merged to `main`.  
> **Scope:** an IPv4 BGP Route Reflector CNF for Kubernetes, plus the external lab behavior required to prove its function.  
> **Governance:** [PROJECT_GOVERNANCE.md](PROJECT_GOVERNANCE.md). Architecture: [architecture.md](architecture.md).

## 1. Objective and boundaries

Provide **two independent FRRouting Route Reflector instances** as Kubernetes CNF Pods. Each reflects IPv4 unicast iBGP routes among four RR clients. OSPFv2 supplies reachability to router loopbacks; separate RR-client transit connectivity provides the **data plane**, so an RR is **never an IP transit router**.

The repository delivers the RR container, Helm Chart, Multus NAD definitions, example configuration, and tests. The four external RR clients, their attached eBGP test peers, external switch, and client-to-client transit fabric are **lab dependencies**; the RR Chart is not their lifecycle authority.

Do not assume that the lab's example ASNs, CIDRs, VLAN IDs, NIC names, external systems, or credentials are portable or appropriate to publish. Keep real company-specific values outside the public repository.

## 2. Accepted-at-discussion design requirements

IDs here retain the numbering used during architecture discussions. This PR proposes their canonical written form; approval of this PR makes them accepted requirements.

### RR / routing

| ID | Requirement |
|---|---|
| R-001 | CNF implements a **BGP Route Reflector** using FRRouting. |
| R-002 | Exactly **two** RR instances are in the initial lab configuration: RR-01 and RR-02. |
| R-003 | CNF external routing is **IPv4 only**. Do not enable OSPFv3 or IPv6 BGP address families in the initial scope. |
| R-004 | Use **OSPFv2** as the IGP for loopback reachability. |
| R-005 | OSPF adjacency on each **RR-to-client** connection is **point-to-point**. This does not predetermine the OSPF type of a separate client-only transit link. |
| R-006 | Advertise router **loopback /32** reachability through OSPF. Do not use OSPF to distribute test service/customer prefixes. |
| R-007 | Use **iBGP IPv4 unicast** for route exchange via the RRs. |
| R-008 | Establish iBGP sessions using the router **loopback addresses**, not the ephemeral Pod primary address. |
| R-009 | Each RR client establishes an iBGP session with **both** RRs. |
| R-026 | The four RR clients advertise **distinct IPv4 prefixes** via iBGP; each remaining client must be able to learn the others' prefixes by reflection. |
| R-027 | RRs **must not forward IP transit traffic** between RR clients or test networks. |
| R-029 | An RR preserves the reflected route's **BGP NEXT_HOP**; NEXT_HOP reachability must be provided outside the RR data plane. |
| R-030 | A loss of one RR does not remove the physical/logical client-to-client data-plane transit path. **No assertion of indefinite BGP route retention** is made for loss of both RRs. |

### Kubernetes / network attachment

| ID | Requirement |
|---|---|
| R-010 | RR CNFs run on **Kubernetes**. |
| R-011 | The Kubernetes primary CNI is **Calico** (environment context, not a requirement that the RR directly use it for external routing). |
| R-012 | The cluster has **Multus** available for secondary Pod interfaces. |
| R-013 | External RR routing connectivity is through **Multus secondary interfaces**. |
| R-014 | Each target Worker has **one physical NIC** available for external RR traffic. |
| R-015 | Use **IEEE 802.1Q VLANs** on the physical NIC to separate L2 segments. |
| R-020 | The target Kubernetes cluster has **two eligible Worker Nodes** for the RRs. |
| R-021 | Pin **one RR to each Worker**, with distinct placements. |
| R-022 | Create each RR as a **directly managed Pod** (`kind: Pod`), rather than an application workload managed by a Deployment/StatefulSet. |
| R-023 | Pod-to-Worker binding is deterministic and fixed under the initial placement policy. |
| R-024 | No Deployment/StatefulSet controller performs automatic RR migration or recreation. Kubelet container restart is a separate behavior. |
| R-025 | A **Helm Chart** renders/manages the direct Pod resources and associated configuration. |
| R-031 | **Helm** declaratively manages RR external connections through **Multus NetworkAttachmentDefinition (NAD)** resources. |

### RR clients and their connections

| ID | Requirement |
|---|---|
| R-016 | The lab has **four RR clients**, Client 1–4. |
| R-017 | Every RR-to-client P2P link uses IPv4 **/31** addressing. |
| R-018 | Each RR-to-client OSPF adjacency uses the P2P link. |
| R-019 | Each independent RR-to-client L2 segment uses a dedicated VLAN. |
| R-028 | Client-to-client packets use **a separate transit network**, not an RR. |

## 3. Derived and additional requirements

The following make explicit other decisions from the conversations. They are not a license to decide the pending parameters in section 5.

| ID | Requirement |
|---|---|
| R-032 | Configure both RRs with the **same BGP Cluster ID**, but a **distinct BGP Router ID and loopback identity** per RR. |
| R-033 | Configure **no RR-to-RR iBGP session** and **no RR-specific interconnect VLAN** in this design. Cluster ID does not establish a cluster-control connection or state synchronization. |
| R-034 | Each RR has **four distinct VLAN-backed /31 secondary interfaces** to the four clients, giving **eight RR-to-client VLANs/links total** across the two Workers. |
| R-035 | Use the **VLAN CNI plugin through Multus**, without requiring a macvlan/ipvlan layer for the initial one-Pod-per-Worker topology. |
| R-036 | Each Client i has a **separate L3 segment and eBGP session** with its respective Test i; the four Client-to-Test segments are independent from each other and from the client transit segment. Test peers do not participate in OSPF. |
| R-037 | RR clients connect over an independent **client-to-client data-plane transit network** that provides reachability to BGP NEXT_HOPs without RR packet forwarding. The exact transit topology and OSPF network type remain open. |
| R-038 | Assign network, BGP, OSPF, and Pod configuration from a **single declared source** (Helm values or a canonical input rendered into Helm values); do not independently hand-maintain contradictory NAD, Pod, and FRR mappings. |
| R-039 | Keep the public OSS portable and **exclude private organization-specific topology, addresses, credentials, and logs** from commits and release artifacts. |
| R-040 | Do not allow stale/orphaned Pod interfaces, configuration mutation, or Worker failure to silently change an RR's **logical identity**. Define and validate the lifecycle behavior before claiming recovery support. |

## 4. Non-goals for the initial target

- IP transit/forwarding performed by the RR Pods.
- RR-to-RR state synchronization, heartbeat, leader election, failover controller, or RR interconnection VLAN.
- HA scheduling or automatic migration of an RR Pod across Workers.
- Operating the four RR clients, four test peers, or the lab switches as a managed feature of the RR Helm release.
- IPv6 external routing, OSPFv3, SR-IOV, DPDK, or a generalized CNF operator/framework.
- Claiming production readiness before implementation, security review, end-to-end testing, and an approved release.

## 5. Unresolved parameters and technical design decisions

**Do not silently turn these into accepted requirements.** They must be resolved in a task-scoped architecture/detail-design decision before implementation that depends on them.

| Topic | Pending decision or fact |
|---|---|
| Addressing | RR/Client/Test loopback addresses; link CIDRs; actual VLAN IDs; non-overlap policy. |
| AS / BGP | Internal ASN, external peer ASNs, cluster ID value, route policies, maximum prefixes, authentication if required. |
| OSPF | Area ID, cost/metric model, stub-router / max-metric policy, link failure convergence, authentication if required. |
| Client transit | One shared VLAN vs P2P topology, whether/how OSPF runs there, and loss-of-transit behavior. |
| NEXT_HOP | Where and how a client makes eBGP-learned route NEXT_HOP reachable by all other clients (candidate: next-hop-self toward the RRs using the client loopback). Verify actual FRR behavior. |
| RR forwarding prohibition | Exact kernel sysctl, FRR route-install and OSPF constraints, and packet-test proof for normal and failure states. |
| Kubernetes / VLAN | Actual Worker labels, physical master interface names, plugin versions, requested capabilities, IPAM and interface lifecycle/recovery actions. |
| Container / Helm | Image base/version, FRR daemon lifecycle, health checks, configuration update mechanism, chart validation schema, security context. |
| Operations | Bootstrap sequence, upgrade/downgrade, deletion/recovery, rollback, expected convergence timing, observability. |
| Distribution | Public OSS license and its prerequisites; container/Chart registries, versioning, signing/digests, release policy. |

## 6. Traceability and acceptance

[architecture.md](architecture.md) explains how the accepted architecture satisfies these requirements. [network-design.md](network-design.md) owns topology semantics and the distinction between physical links, VLAN, OSPF adjacency, and BGP peering. [acceptance-criteria.md](acceptance-criteria.md) defines evidence to be collected by Codex and reviewed by Chat/Owner.

**Rule:** an implementation PASS is not a substitute for satisfying the specified routing, separation, and failure invariants. Exact configuration and measured results are not asserted in this requirements document.
