# Acceptance criteria and verification plan — frr-route-reflector

> **Status: Proposed. No test has been executed by Chat as part of this document.**  
> Requirements: [requirements.md](requirements.md). Architecture: [architecture.md](architecture.md). Topology: [network-design.md](network-design.md).

## 1. Verification contract

A successful container build, Pod `Running`, Helm `template`, FRR daemon start, OSPF `Full`, or BGP `Established` is **necessary evidence for its specific layer**, not acceptance of the full system.

Use **three gates** to avoid widening the current development scope without need:

| Gate | Entry/goal | Completion |
|---|---|---|
| G-1 Design | Capture accepted requirements and logical topology | Owner accepts requirements, architecture, open-decision list and these evidence obligations on `main` |
| G-2 Implementation | Produce RR container, Helm/NAD/FRR configuration and deterministic validations | Code meets task-specific invariants and has automated checks; unresolved G-3 environment claims are not reported as PASS |
| G-3 Integrated lab | Deploy to two Workers, integrate four clients and four test peers | Demonstrate routing control plane, client-only forwarding, failure behavior and cleanup with captured evidence |

A task that needs an unresolved architecture decision must **STOP** and return a minimal decision request, not silently guess.

## 2. Design and static artifact acceptance

| ID | Requirement coverage | Evidence / expected result |
|---|---|---|
| A-001 | R-001–R-009, R-032, R-033 | FRR config renders 2 RR identities, 1 shared Cluster ID, 4 RR clients per RR, IPv4 unicast, OSPFv2 and **no RR↔RR BGP peer** |
| A-002 | R-020–R-025 | Helm renders exactly 2 bare `Pod` objects, each with deterministic distinct Worker assignment; no `Deployment`, `StatefulSet` or hidden RR rescheduling controller |
| A-003 | R-013–R-019, R-031, R-034–R-035 | Helm renders 8 distinct NADs with VLAN CNI, 4 Multus references per Pod, static /31 link assignment and no conflicting interface mappings |
| A-004 | R-038 | Given one canonical values input, NAD VLAN/IP/IF definitions and FRR interface references derive consistently; conflicting/invalid input is rejected where enforceable |
| A-005 | R-003, R-006 | No configured OSPFv3/IPv6 BGP address family or unintended redistribution of test/customer BGP prefixes into OSPF |
| A-006 | R-039 | No internal organization secrets/configs/hostnames/credentials, no misleading production values; publishable examples and license/dependency review |
| A-007 | R-040 | Pod identity and lifecycle plan specifies shutdown, updates, interface cleanup, failure and recovery semantics rather than assuming Deployment-style reconciliation |

The code stage must include repeatable evidence such as `helm lint`, `helm template`, schema validation, rendered-object checks and FRR configuration validation. Exactly which command validates FRR must be demonstrated against the selected FRR version; do not invent PASS output.

## 3. Integrated control-plane tests

| ID | Scenario | Expected outcome |
|---|---|---|
| T-001 | Multus/NAD attachment, both Workers | Each RR has Calico primary and four intended VLAN secondary interfaces; correct VLAN IDs, /31 addresses and outside peer reachability |
| T-002 | Normal OSPF adjacency | RR-01 and RR-02 each have **four Full P2P OSPF adjacencies**; all required loopback /32 routes are usable |
| T-003 | Normal iBGP | RR-01 and RR-02 each have **four Established client sessions**; each client peers with both RRs using loopback endpoints |
| T-004 | Route reflection | Four distinguishable prefixes are advertised from the appropriate clients; remaining clients learn each other's routes through RR reflection |
| T-005 | BGP attributes | Reflection preserves expected NEXT_HOP; no unintended RR NEXT_HOP substitution, loops or withdrawn/unreachable routes |
| T-006 | Test eBGP | Each Test i ↔ Client i establishes eBGP only on its dedicated segment, no test OSPF; expected IPv4 route exchange/policy is observed |
| T-007 | NEXT_HOP recursion | Remote client resolves a reflected BGP NEXT_HOP to an actual **client-only transit** forwarding adjacency, not an RR interface |

Proof examples: FRR `show ip ospf neighbor`, `show ip route`, `show bgp ipv4 unicast`, `show bgp ipv4 unicast summary`, actual Linux Pod route/interface state, BGP attributes and relevant event logs. Use the selected FRR version's supported CLI and store sanitized evidence, not guessed output.

## 4. Data-plane and failure tests

| ID | Scenario | Expected outcome |
|---|---|---|
| T-008 | Test 1 to Test 2 (and representative other pairs) | Packets follow **Test → Client → Client Transit → Client → Test**, with no RR transit forwarding |
| T-009 | RR nontransit verification | Forwarding settings plus route/packet inspection show no client-to-client IP transit through either RR, including a deliberate would-be-transit probe |
| T-010 | RR-01 Pod/Worker loss | RR-02 remains available for four-client iBGP reflection; client-to-client transit connectivity is not physically dependent on RR-01 |
| T-011 | RR-02 Pod/Worker loss | Symmetric expectation to T-010 |
| T-012 | RR recovery / reattachment | The logical RR returns without duplicate loopback identity, lingering VLAN interfaces, stale NAD attachment or unobserved routing inconsistency |
| T-013 | Loss of client transit | No automatic reroute of **user packets** through an RR. Loss or withdrawal of data connectivity is reported rather than concealed |
| T-014 | Loss of both RRs | Client-to-client transit topology remains separate, but **no assumption that BGP-learned routes survive session/hold expiry**; record behavior without calling route retention a requirement |
| T-015 | Pod delete / spec update | No undocumented automatic replacement or migration of a bare Pod; any manual reinstall/recovery process is explicit and tested |
| T-016 | VLAN CNI lifecycle | Add, normal delete and failure/retry paths are checked for namespace-specific attachment correctness and cleanup; defects are recorded as defects |

Check both the **selected route** and the **packet actually forwarded**. An OSPF route preferring the Client Transit does not alone prove that an RR can never become a transit path under a failed-link topology. Ensure the acceptance topology and failure tests exercise that distinction.

## 5. Evidence format for Codex PR

An implementation PR should provide:

1. **Scope**: linked accepted requirements / ADRs and exact changed files.
2. **Static tests**: command, environment/tool version, outcome and log/artifact reference.
3. **Lab tests**: topology binding revision, FRR/Kubernetes/CNI versions, command/packet path evidence and observed result.
4. **Invariants**: which of I-01–I-10 were checked and with what observations.
5. **Negative tests**: rejected invalid input, unexpected transit packet, degraded-node behavior where applicable.
6. **Unverified**: explicit `NOT RUN`, `BLOCKED`, or remaining limitations. **Never report an unexecuted test as PASS.**

When evidence could reveal private lab information, redact or summarize before posting to public GitHub, while keeping the original local evidence accessible to the Owner.

## 6. Criteria intentionally not invented

Before executing measured convergence/HA tests, the project must decide the acceptable recovery/withdrawal timings, OSPF metrics, relevant hold/BFD policy (if any), and test stimulus. Likewise, before release it must decide the license, vulnerability baseline, image/Chart provenance and version/digest pinning.

They remain **pending** rather than quietly becoming requirements. A design is not accepted merely because the test matrix is long; every executed test must contribute directly to the current Phase objective.
