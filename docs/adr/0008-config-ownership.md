# ADR 0008 — Helm values own FRR boot configuration

**Status:** Proposed; becomes accepted only when merged to `main`.

## Context

The RR Helm release must render two Pods, eight Multus/VLAN NADs and per-RR FRR configuration, without independently maintained interface definitions. A ConfigMap mounted read-only may not satisfy the selected FRR distribution's runtime file/ownership needs. Mutable live configuration creates divergence between accepted Git state and the running routing process.

## Decision

1. **Helm values are authoritative for all RR routing identities, peers and interfaces.** Templates deterministically derive two per-RR integrated FRR configurations, eight NADs and matching Pod annotations.
2. Use the FRR **integrated `frr.conf`** convention rather than maintaining parallel daemon-specific configuration sources. Only required FRR services run: zebra, ospfd, bgpd and the distribution's essential supervisor/configuration helpers.
3. ConfigMaps are the immutable *desired-configuration snapshot*. Runtime `frr.conf` may be copied to a Pod-private writable volume on start if FRR requires it; edits with `vtysh write` must not be accepted as the configuration source and are overwritten on replacement.
4. The same config sources configure unique RR loopbacks, OSPF P2P interfaces and shared BGP Cluster ID; no separate handwritten peer list is supplied through another template.
5. Any effective configuration change is a **reviewed new desired snapshot** requiring explicit, controlled Pod restart/replacement. A Helm-rendered annotation or changing a ConfigMap is **not** a built-in live reload mechanism.
6. The RR Chart never creates or modifies external Clients, Tests or the Client Transit network.

## Rationale and consequences

One declarative source makes the mapping `(RR, Client) → (Worker, VLAN, Pod IF, /31, OSPF adjacency, iBGP peer)` finite and testable. ConfigMap-per-RR provides simple change review and runtime inspection without an invented controller. Helm and the operator must explicitly recognize Pod immutability/replacement limitations.

**Required evidence:** identical input renders identical FRR/NAD/Pod bindings; bad values fail validation; startup consumes exact accepted bytes; a restart does not silently retain runtime edits; and security/readiness gates run before FRR serving.

Reference: [FRR integrated configuration](https://docs.frrouting.org/en/latest/basic.html).

Authority: [implementation-contract.md](../implementation-contract.md).
