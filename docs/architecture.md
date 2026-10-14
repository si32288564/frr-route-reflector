# Architecture — frr-route-reflector

> **Authority:** The reviewed `main` version is the accepted Architecture; changes on a PR branch remain proposals.  
> Normative requirements: [requirements.md](requirements.md). Topology authority: [network-design.md](network-design.md). Proof obligations: [acceptance-criteria.md](acceptance-criteria.md). Governance: [PROJECT_GOVERNANCE.md](PROJECT_GOVERNANCE.md).

## 1. System boundary and objective

`frr-route-reflector` is a **public, reusable FRRouting IPv4 Route Reflector CNF** deployed on Kubernetes. The CNF reflects control-plane routing information; it **must not serve as an IP transit data-plane device**. The external lab has four RR clients, each connected to its own eBGP test peer, and a separate client-to-client data-plane transit network.

The **RR Helm release** owns the RR Pods, RR-attached Multus NADs, and the RR configuration artifacts it renders. The **external lab** owns the RR clients, tests peers, transit connectivity, switch port/VLAN provisioning, Kubernetes cluster, Calico, Multus and CNI binary prerequisites. The public Chart must not require knowledge of employer-specific topology.

## 2. Logical components and relations

| Entity / set | Cardinality | Role / invariant |
|---|---:|---|
| RR CNF | 2 | `RR-01`, `RR-02`; independent route reflection with common Cluster ID |
| Kubernetes Worker | 2 | One RR assigned to each Worker; no automatic cross-Worker relocation |
| External RR client | 4 | Client 1–4; each has iBGP to both RRs |
| Test peer | 4 | Test i ↔ Client i via a dedicated eBGP segment; no test-peer OSPF |
| RR↔Client logical P2P link | 8 | Each of the 2 × 4 relationships has its own /31 and VLAN |
| RR-side Multus interface / NAD | 8 / 8 | Four secondary interfaces per RR, backed by VLAN CNI |
| Client-to-client transit network | 1 logical function | One independent shared client-only IPv4 /29 VLAN, OSPFv2 broadcast (ADR 0005) |
| Client↔Test network | 4 | Independent eBGP segments outside the RR Chart's responsibility |

This cardinality is **about different object classes**. One VLAN is not necessarily one BGP session: iBGP endpoints are loopbacks, and OSPF adjacencies are established over the /31-connected links.

## 3. Functional planes

### 3.1 OSPF — underlay reachability

- The initial RR-to-client IGP is **OSPFv2 point-to-point** on every VLAN-backed /31 link.
- OSPF advertises router loopback /32 prefixes sufficient to establish loopback-sourced iBGP and resolve BGP NEXT_HOPs.
- It does **not** carry the distinct service/test prefixes that the clients advertise through BGP.
- The external four-client transit fabric is one IPv4 /29 shared VLAN with **OSPFv2 broadcast**. This is distinct from the eight RR↔Client OSPF P2P /31 links; both participate in the same initial OSPF area, and all clients advertise their loopbacks /32.
- The OSPF graph **must not create a usable client-to-client data path through either RR**. Specify constraints and verify this under failures as well as during steady state.

### 3.2 BGP — control plane

- Each RR runs IPv4-unicast iBGP with **all four** RR clients, addressed by stable loopbacks.
- Both RRs share one **Cluster ID** but use distinct **Router IDs** and loopbacks.
- Clients are configured as RR clients **on the RR side**. Clients need ordinary iBGP peers to the two RR loopbacks; they do not require a local Cluster ID to join the topology.
- No RR↔RR iBGP session and no cluster-state synchronization or RR-dedicated VLAN.
- Reflect accepted client routes without changing BGP NEXT_HOP on the RR.
- Four external clients originate/redistribute or learn distinct test prefixes and advertise them to both RRs; BGP policies and origin mechanics are detailed design decisions.

**A common Cluster ID is a route-reflection loop-prevention identity, not a Kubernetes-style HA cluster membership protocol.** The two RR instances are independent active-active control-plane peers, not a leader/follower pair.

### 3.3 Data plane — external to RR

For example, for an advertised Test 2 prefix:

```text
Control-plane advertisement:
Test 2 --eBGP--> Client 2 --iBGP--> RR-01/RR-02 --reflection--> Client 1

Data-plane packets:
Test 1 --> Client 1 --> [client-to-client Transit] --> Client 2 --> Test 2
```

For eBGP-learned Test routes, each originating Client sets outbound iBGP NEXT_HOP to **its own loopback** toward both RR peers; each RR reflects the attribute unchanged. The receiving client resolves the originating client's loopback through OSPF using the **client-only transit VLAN**. The FRR implementation must prove the advertised NEXT_HOP and actual FIB recursion.

**Hard invariant:** forwarding of client↔client/test↔test transit packets by any RR is prohibited. Enforce and verify `net.ipv4.ip_forward = 0` **inside the RR Pod network namespace**, independent of Worker-host forwarding. Also advertise `max-metric router-lsa administrative` from each RR and prefer `bgp no-rib` to avoid a service-prefix FIB. OSPF max-metric is a preference, **not a guarantee** that no client ever selects RR as its next hop. If client transit disappears, traffic loss / blackholing is acceptable **fail-closed** behavior, but RR must never forward the packets. Verify both normal and failure conditions by packet observation.

## 4. Kubernetes CNF realization

```text
Worker-01 (fixed)                      Worker-02 (fixed)
  RR-01: kind=Pod                        RR-02: kind=Pod
    lo    : stable RR loopback             lo    : stable RR loopback
    eth0  : Calico primary                 eth0  : Calico primary
    net1-4: Multus VLAN CNI                net1-4: Multus VLAN CNI
       |                                       |
  single external trunk NIC              single external trunk NIC
       |                                       |
  4 VLANs / 4 /31 links                  4 VLANs / 4 /31 links
       \                 external L2 switch  /
        \---- Client 1 .. Client 4 ---------/
```

- **Bare Pods** (`kind: Pod`) are fixed to distinct Workers; no Deployment or StatefulSet reconciles a deleted Pod or schedules another node on failure.
- Kubelet **may restart a container** within an existing Pod according to its restart policy. That is not Pod-level redundancy and does not make a lost Pod self-recreating.
- Stable router identity (loopback, BGP/OSPF Router ID, BGP Cluster ID) belongs to **the logical RR**, not a randomly assigned Calico primary Pod IP.
- Each Worker contributes **one external physical interface** carrying a VLAN trunk; VLAN CNI attaches the selected VLAN interface into the RR Pod's network namespace via Multus.
- No macvlan/ipvlan stacking is needed for this initial one-RR-per-Worker design. This selection is not a prohibition on other CNFs using those plugins in the future.
- No Pod fallback to `eth0`/Calico for external OSPF or iBGP traffic without explicit design approval.

### 4.1 Configuration ownership and projection

The configuration graph is:

```text
Canonical declarative input (e.g. Helm values, schema-validated)
    ├── Pod objects / fixed-node assignment
    ├── Multus network annotations / interface names
    ├── VLAN-CNI NADs / static /31 addresses
    └── FRR configuration (zebra, ospfd, bgpd)
```

For each `(RR, Client)` relation, the VLAN ID, master, Pod-side interface, /31 address, OSPF participation, and routing identity must agree. **Do not create separate manually maintained copies of the same interface mapping.** The specific mechanism of generating FRR configuration (Helm-rendered ConfigMap vs image-side generation) remains open and may not be silently decided by Codex when it changes Architecture authority.

### 4.2 Lifecycle boundary

- Node failure does not grant permission to relocate an RR automatically.
- Pod/container restart must not cause duplicate or orphaned interface assignments, ambiguous logical RR identity, or undetected routing outages.
- Changes to direct Pod configuration may require delete/recreate. This is not treated as a generic zero-downtime rolling Deployment.
- Recovery, safe replacement, old-instance fencing where necessary, and the scope of rollback need an explicit task-level design and tests; do not claim these work merely because a Helm render or Pod start passes.

## 5. Architecture invariants

| Invariant | Violation example |
|---|---|
| I-01: Each logical RR has stable, unique Router ID and loopback | Identity changes with primary Pod IP |
| I-02: Both RRs share one Cluster ID but operate independently | Addition of implicit cluster heartbeat |
| I-03: All four clients can peer with both RRs | A client depends on only one RR |
| I-04: RR may not be IP transit | Client data is forwarded via RR on failure |
| I-05: OSPF distributes only required underlay reachability | Test service prefixes leaked into IGP |
| I-06: A reflected route retains its next hop | RR performs an unapproved next-hop-self |
| I-07: Client transit is external to RR | Loss of RR also removes physical client transit |
| I-08: NAD/Pod/FRR derived artifacts agree with one declared mapping | VLAN or IP mismatch between NAD and ospfd |
| I-09: Public repository cannot embed private employer configuration | A real company hostname in examples |
| I-10: Accepted architecture precedes task-scoped implementation | Codex invents topology or failover semantics |

## 6. Explicitly unresolved Architecture edges

Before building features that depend on them, close only the relevant decisions below:

1. **Resolved in ADR 0005–0007 (subject to this PR's acceptance):** shared Client Transit VLAN /29 with OSPF broadcast; client-side next-hop-self for Test-eBGP routes; RR Pod-local IP forwarding disabled with OSPF administrative max-metric, plus `bgp no-rib` as default control-only mode. **Loss of Client Transit may cause fail-closed traffic loss.**
2. **BGP/OSPF parameterization:** actual ASN(s), OSPF area ID and metrics, router addresses, authentication, prefix/route policies and failure timers.
3. **Runtime proof and permissions:** safe Pod-local sysctl enforcement, Linux capabilities/security context, FRR command behavior in selected version, nontransit packet evidence.
4. **Kubernetes/Helm lifecycle:** node selection, restart/recovery, CNI interface cleanup and configuration changes.
5. **Publishing:** license, dependency versions, image/Chart delivery and reproducible releases.

Architecture decisions [ADR 0005](adr/0005-client-transit-broadcast.md), [ADR 0006](adr/0006-client-next-hop-self.md), and [ADR 0007](adr/0007-rr-nontransit-enforcement.md) hold rationale; topology facts live in [network-design.md](network-design.md).

Proposals and examples may be written to support discussion, but must be labelled as such. The exact IPs, VLAN IDs, master names, ASN values, and timing targets are **not** agreed here.

## 7. Change control

Requirement changes go to [requirements.md](requirements.md); topology/connection semantics to [network-design.md](network-design.md); acceptance obligations to [acceptance-criteria.md](acceptance-criteria.md). ADRs, where used, record why an accepted choice was made rather than becoming a second independent source for its technical values.

This document does **not** attest to a deployed environment or test run. Acceptance requires a GitHub PR reviewed against [PROJECT_GOVERNANCE.md](PROJECT_GOVERNANCE.md).
