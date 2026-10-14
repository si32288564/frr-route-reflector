# ADR 0001 — Two RRs, one Route Reflector Cluster ID

- **Authority status:** Proposed on an unmerged PR branch; accepted only after Owner review and merge to `main`.
- **Context:** Four RR clients must learn each other's distinct IPv4 prefixes. Two RR instances provide redundant reflection.
- **Decision:** Configure two independent RRs, each peered to all four clients, with the **same Cluster ID**, separate router identities, **no RR-to-RR iBGP**, and **no RR-specific interconnect VLAN**.
- **Rationale:** BGP route-reflection Cluster ID is a loop-prevention attribute used in reflected routes; it is not a membership, heartbeat, synchronization, or automatic HA mechanism. Dual-homing all four clients to both RRs makes a direct RR-to-RR route exchange unnecessary for this initial topology.
- **Consequences:** Both RRs reflect independently; a client missing one RR session loses redundancy. Cluster ID equality does not promise equal route state or convergence timing. A future asymmetric client topology requires a new design review.
- **Rejected alternatives:** Explicit RR-to-RR iBGP solely to emulate cluster synchronization; separate Cluster IDs without a demonstrated requirement.
- **Authority:** [Requirements](../requirements.md) R-002, R-009, R-032, R-033; [Architecture](../architecture.md).
