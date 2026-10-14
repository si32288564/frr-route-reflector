# ADR 0002 — Direct Pods with fixed Worker placement

- **Authority status:** Proposed on an unmerged PR branch; accepted only after Owner review and merge to `main`.
- **Context:** Each RR has a stable routing identity and four external /31 VLAN attachments bound to an eligible Worker.
- **Decision:** Deploy exactly one **direct Pod** per Worker, with deterministic placement, through Helm. Do not use a Deployment or StatefulSet and do not automatically relocate an RR following node failure.
- **Rationale:** Avoid an implicit reconciliation/rescheduling behavior that might break node-bound VLAN and routing identity assumptions. RR service redundancy is obtained through dual iBGP peers, not Pod replicas or automatic migration.
- **Consequences:** Kubelet can restart failed containers, but Pod deletion or Worker loss may require explicit operational recovery. Pod replacement, idempotence, stale CNI attachments, and fencing must be verified before recovery is considered supported.
- **Rejected alternatives:** Generic `replicas: 2` Deployment with freely relocatable Pods; automatic failover controller without a proven need.
- **Authority:** [Requirements](../requirements.md) R-020–R-025, R-040; [Architecture](../architecture.md).
