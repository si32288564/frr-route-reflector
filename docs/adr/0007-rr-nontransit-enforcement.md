# ADR 0007 — RR IP non-transit enforcement

Status: Proposed; accepted only after Owner review and merge to main.

## Decision

RR Pods are control-plane-only routers. **No client or test packet may be forwarded between an RR's interfaces**.

1. Enforce and verify `net.ipv4.ip_forward = 0` **inside each RR Pod network namespace**, before making routing service operational and after restart. Never change a Worker-wide forwarding setting as a workaround, and do not use host networking.
2. Configure FRR OSPF `max-metric router-lsa administrative` permanently, so SPF normally avoids the RR as a transit vertex while permitting the RR's own loopback reachability. Maintain all four P2P OSPF adjacencies.
3. Use FRR `bgp no-rib` as a control-only default so learned BGP service prefixes are not installed into Zebra/the kernel FIB. Verify the selected FRR version still reflects routes correctly and supports necessary BGP next-hop tracking. This is **defense in depth** and not a substitute for disabling IP forwarding.
4. OSPF must not redistribute external Test/customer prefixes. RR must not rewrite BGP NEXT_HOP.
5. If the implementation cannot enforce or verify the Pod-local forwarding gate, it must fail closed: do not expose a ready/operational RR. Codex may choose the Pod-local implementation mechanism, but changing cluster security policy requires explicit Owner acceptance.

## Limits

OSPF max-metric discourages transit; it **cannot categorically prevent** a client from calculating a path via an RR if all client-only transit alternatives disappear. With the client transit VLAN down, packets may be dropped, even while BGP or OSPF shows partial reachability. This is explicitly acceptable **fail-closed unavailability**, not a promise of data-plane resilience. The lab must report/observe this failure rather than claim seamless rerouting.

Kubernetes does not list `net.ipv4.ip_forward` among automatically admitted safe Pod sysctls. Do not assume direct Pod securityContext.sysctls setting will work in every cluster; verify admission capabilities, namespace isolation and kernel sysctl state.

## Acceptance evidence

Check Pod-local forwarding value 0, actual max-metric Router-LSA, reflection with BGP no-rib, and Client FIB path through Transit while healthy. Conduct a deliberate Client→RR→Client transit probe and repeat after removing the Client Transit path: no packet may be forwarded by either RR. Verify both Pod restart and failure behavior.

Sources:
- https://docs.frrouting.org/en/latest/ospfd.html
- https://docs.frrouting.org/en/latest/bgp.html
- https://www.kernel.org/doc/html/latest/networking/ip-sysctl.html
- https://kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster/
- https://www.rfc-editor.org/rfc/rfc3137

Authority: [architecture.md](../architecture.md); [requirements.md](../requirements.md).
