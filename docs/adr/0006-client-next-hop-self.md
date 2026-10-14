# ADR 0006 — Client-side eBGP-to-iBGP NEXT_HOP

Status: Proposed; accepted only after Owner review and merge to main.

Each Test i advertises an IPv4 prefix to Client i by eBGP on a segment not participating in OSPF. The original eBGP NEXT_HOP may not be reachable by other RR clients. Therefore, each Client i sets NEXT_HOP to its own stable loopback address when advertising routes learned from Test i to **both** iBGP RR peers.

Use the FRR behavior represented by `neighbor <RR> next-hop-self` (without `force`) together with a loopback-sourced iBGP session; verify the actual UPDATE's NEXT_HOP in the selected FRR version. `force` would also alter iBGP-learned routes and is not part of this policy. The RRs reflect without altering NEXT_HOP.

Receiving clients resolve the origin Client loopback by OSPF over the independent Client Transit VLAN. On the Test-facing eBGP session, verify reverse route advertisement and reachable next hop separately.

Acceptance requires evidence of: received eBGP prefix, outbound Client→RR NEXT_HOP, RR-reflected NEXT_HOP, receiving Client RIB/FIB recursion via client-only transit, and actual Test-to-Test packets. Established BGP sessions alone do not suffice.

This is an external-lab client-side configuration obligation, not a new RR Helm Chart feature.

Sources: https://docs.frrouting.org/en/latest/bgp.html and https://www.rfc-editor.org/rfc/rfc4456

Authority: [network-design.md](../network-design.md) and [requirements.md](../requirements.md).
