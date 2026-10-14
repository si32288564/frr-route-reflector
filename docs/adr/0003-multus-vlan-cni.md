# ADR 0003 — Multus with VLAN CNI

- **Authority status:** Proposed on an unmerged PR branch; accepted only after Owner review and merge to `main`.
- **Context:** Each Worker provides one trunk-capable physical NIC; its RR needs four distinct external VLAN segments, each dedicated to one /31 P2P client link.
- **Decision:** Use Multus secondary interfaces backed by **VLAN CNI** and Helm-managed NADs. Each Worker receives one RR Pod with four independently assigned VLANs; eight RR↔Client links/NADs in total.
- **Rationale:** VLAN CNI directly attaches VLAN interfaces without a second macvlan/ipvlan abstraction in this one-Pod-per-Worker topology.
- **Consequences:** Correct VLAN trunk configuration, CNI binary availability, unique per-Worker VLAN attachments, static IP assignment and CNI cleanup are environmental/operational obligations. Multiple Pods on the same Worker needing the same VLAN could require a future design change.
- **Rejected alternatives:** macvlan or ipvlan stacked on precreated host VLAN subinterfaces without an initial requirement for sharing a VLAN among Pods.
- **Authority:** [Requirements](../requirements.md) R-013–R-019, R-031, R-034–R-035; [Network design](../network-design.md).
