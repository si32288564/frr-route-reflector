# Network design — frr-route-reflector

> **Authority status:** On an unmerged PR branch this is a proposal; after Owner review and merge to `main`, it is the accepted topology authority. Actual environment values remain unassigned.  
> Requirements: [requirements.md](requirements.md). System behavior: [architecture.md](architecture.md). Acceptance: [acceptance-criteria.md](acceptance-criteria.md).

## 1. Topology and interface sets

The external network is composed of **three separate functions**:

1. **RR-to-client control links:** eight physical/logical VLAN-backed IPv4 /31 connections, OSPFv2 P2P on each; iBGP is formed between loopbacks reachable across the IGP.
2. **Client-to-test eBGP links:** four *individual* segments, one Client i ↔ Test i; Test nodes do not run OSPF.
3. **Client-to-client transit fabric:** an independent routing/data-plane connection among all four Clients, never relying on either RR for transit forwarding. Its physical topology/OSPF type have not been accepted.

```text
       Worker-01                                  Worker-02
       RR-01 Pod                                  RR-02 Pod
       [4 Multus/VLAN IFs]                        [4 Multus/VLAN IFs]
          | | | |                                    | | | |
          | | | +--- P2P /31 VLAN -> Client 4 <-------+ | | |
          | | +----- P2P /31 VLAN -> Client 3 <---------+ | |
          | +------- P2P /31 VLAN -> Client 2 <-----------+ |
          +--------- P2P /31 VLAN -> Client 1 <-------------+

        Client 1 ---+                                +--- Client 4
        Client 2 ---+-- [client-to-client Transit] --+--- Client 3
             |                                               |
            ...           (data plane only uses Clients)     ...

       Client 1 --eBGP dedicated segment-- Test 1
       Client 2 --eBGP dedicated segment-- Test 2
       Client 3 --eBGP dedicated segment-- Test 3
       Client 4 --eBGP dedicated segment-- Test 4
```

**Diagram semantics:** the RR↔Client links are separate L2/VLAN links, not shared broadcast domains. The diagram is not a physical switch wiring plan; no RR↔RR link is present. The transit fabric is a logical requirement, not yet an accepted single-VLAN realization.

## 2. Eight RR-to-client interface relationships

Each row is **one distinct VLAN and one distinct /31 subnet**. The Pod IF name is scoped *per Pod*; `net1` on RR-01 is not the same interface as `net1` on RR-02. The numeric VLAN labels below are **placeholders**, not assigned IDs.

| RR | Worker | Multus IF | VLAN relation | IPv4 link |
|---|---|---|---|---|
| RR-01 | Worker-01 | net1 | VLAN(RR-01, Client 1) | /31(A1) |
| RR-01 | Worker-01 | net2 | VLAN(RR-01, Client 2) | /31(A2) |
| RR-01 | Worker-01 | net3 | VLAN(RR-01, Client 3) | /31(A3) |
| RR-01 | Worker-01 | net4 | VLAN(RR-01, Client 4) | /31(A4) |
| RR-02 | Worker-02 | net1 | VLAN(RR-02, Client 1) | /31(B1) |
| RR-02 | Worker-02 | net2 | VLAN(RR-02, Client 2) | /31(B2) |
| RR-02 | Worker-02 | net3 | VLAN(RR-02, Client 3) | /31(B3) |
| RR-02 | Worker-02 | net4 | VLAN(RR-02, Client 4) | /31(B4) |

**Do not treat** labels `A1`–`B4` as actual subnet names or VLAN IDs. A later environment binding maps each relation to a real address pair, VLAN ID, parent master, and external switch port.

## 3. VLAN attachment model

```text
Kubernetes Worker
  Calico primary CNI -----------------------> Pod eth0 (K8s management only)
  single trunk physical NIC
      ├── VLAN X1 -- VLAN CNI / Multus NAD --> Pod net1
      ├── VLAN X2 -- VLAN CNI / Multus NAD --> Pod net2
      ├── VLAN X3 -- VLAN CNI / Multus NAD --> Pod net3
      └── VLAN X4 -- VLAN CNI / Multus NAD --> Pod net4
                                               ↕ OSPFv2 P2P to clients
  Pod lo (stable /32) <-------------------------> BGP identity/address
```

The Chart projects a declared `(RR, Client)` mapping into:

- **One NAD per link:** eight total, CNI `type: vlan`, a Worker physical `master`, an assigned `vlanId`, and static IPv4 /31 addressing.
- **One Multus network reference per NAD:** four secondary interfaces per Pod, explicit Pod-facing interface names.
- **FRR configuration:** `ospfd` participates on the matching `netN` and advertises the RR loopback; `bgpd` peers with the clients via loopbacks.

A default gateway should not be fabricated on each /31 external link. Any route to the iBGP endpoint is established through the designed IGP, not by rewriting the Pod's default route to a VLAN segment.

**Environmental prerequisites:** both Workers have the VLAN CNI plugin installed and Multus configured; target physical NIC(s) exist; switches allow the required VLANs on their trunks and carry the correct segment membership to Clients; VLAN uniqueness and IP address non-overlap are validated. A Chart render does **not** prove that these external conditions exist.

## 4. Control-plane versus data-plane path

Assume Test 2 advertises a unique IPv4 prefix to Client 2 via eBGP.

1. Client 2 learns/accepts the external route.
2. Client 2 advertises it via iBGP to **both** RR loopbacks.
3. Each RR reflects it independently to Client 1, 3 and 4, keeping the BGP NEXT_HOP as received by the RR.
4. Client 1 resolves the advertised NEXT_HOP through its IGP/underlay and must select a usable path via **client-to-client Transit**.
5. Test 1 ↔ Test 2 packet traffic follows `Test 1 → Client 1 → Transit → Client 2 → Test 2`, not through the RR Pod.

The **client-side** eBGP-to-iBGP NEXT_HOP rewriting/policy is an unresolved but **necessary design obligation**: the eBGP peer's link address is not automatically reachable from other clients, because Test peers are outside OSPF. A candidate is `next-hop-self` toward the RR peers, sourced from the client's loopback. The exact implementation requires proof using FRR routing state and real traffic, not assumption.

**BGP session path and data path are different.** Receiving a route from RR-01 does not imply that user traffic should use RR-01.

## 5. OSPF topology safety and RR non-transit

- Every RR-client link forms an OSPFv2 P2P adjacency, but this does **not** authorize the RR to transit traffic between links.
- The client transit topology must provide a valid forwarding path to other clients' BGP NEXT_HOPs.
- **Failure behavior matters:** simple cost preferences cannot alone establish a strict no-RR-transit invariant under arbitrary failures.
- Candidate safeguards include disabling IPv4 forwarding **within the RR Pod namespace**, and a suitable OSPF nontransit / max-metric policy. They must be assessed together to prevent normal or failure-state blackholes. No chosen sysctl/FRR CLI is asserted here as accepted.
- The initial design contains **no RR↔RR OSPF adjacency**, no RR↔RR iBGP, and no RR↔RR VLAN. An OSPF link-state database could contain information originated by the other RR via the client OSPF domain; that is not a direct RR-to-RR session.

## 6. Addressing / policy binding to be decided

The next detail-design task must produce **one input table** with, at minimum:

- Each RR, Client and Test loopback/Router ID and ASN identity as applicable.
- For each of eight RR-client links: RR, Client, Worker, NIC master, VLAN ID, /31 pair, Pod IF, OSPF area/cost.
- For each of four eBGP links: client/test relation, segment, addresses, eBGP peer ASNs and route advertisement policy.
- Client transit topology, addresses, IGP use, metrics and nontransit safety proof.
- Route acceptance/export policy, including eBGP-learned prefix NEXT_HOP transformation and any BGP attributes needed.

The values belong in a reusable example/environment binding and/or accepted configuration source. Company-specific real infrastructure values **must never** be added to this public repository.

## 7. Initial topology acceptance conditions

- Eight distinct RR↔Client P2P links and eight correct VLAN attachments can be observed.
- Each RR forms OSPF P2P adjacency with each of four clients; each client can reach both RR loopbacks.
- Four distinct client-originated BGP routes appear at both RRs and are reflected to the other clients.
- BGP NEXT_HOP recursion for a remote client uses the Client Transit fabric.
- A packet probe between test peers does not forward through an RR in either nominal or required failure states.
- Failure of RR-01 alone, or RR-02 alone, leaves the other RR available as a reflector. Removal of an RR never moves client transit into that RR's Pod.

See [acceptance-criteria.md](acceptance-criteria.md) for verification details; this file is topology intent, **not a completed test report**.
