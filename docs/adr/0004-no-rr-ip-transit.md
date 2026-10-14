# ADR 0004 — RRs are not IP transit

- **Authority status:** Proposed on an unmerged PR branch; accepted only after Owner review and merge to `main`.
- **Context:** Four clients each have a separate eBGP-connected test peer. iBGP reflection distributes routes but does not provide a valid client-to-client packet forwarding fabric.
- **Decision:** The RR CNF is a **control-plane-only reflector**. Client-to-client data traffic traverses an **independent Client Transit network**, and RR Pods must never forward transit packets. A reflected BGP NEXT_HOP remains unchanged on the RR.
- **Rationale:** Separating control-plane routing distribution from data-plane forwarding permits direct testing of RR failure without coupling every packet to RR Pod/Worker health.
- **Consequences:** Client-side NEXT_HOP handling, transit topology, OSPF routing policy and namespace-specific forwarding prohibition require further detail design and negative packet tests. Disabling forwarding alone does not imply correct reachability or failure-state convergence.
- **Rejected alternatives:** Routing test traffic through the RR Pods, or adding RR-to-RR links to act as a transit fabric.
- **Authority:** [Requirements](../requirements.md) R-027–R-030, R-036–R-037; [Network design](../network-design.md).
