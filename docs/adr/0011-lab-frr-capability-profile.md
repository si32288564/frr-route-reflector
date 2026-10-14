# ADR 0011 — Lab-only FRR capability profile and explicit admission gate

**Status:** Proposed; not authorized until Owner review and merge to `main`.

## Context and bounded evidence

[ADR 0010](0010-minimal-frr-runtime.md) selected a project-built Alpine 3.24 runtime using distro FRR packages. [Draft PR #6](https://github.com/si32288564/frr-route-reflector/pull/6) documents three tests:

- The upstream Quay FRR 10.3.1 candidate fails `zebra` capability initialization without `CAP_SYS_ADMIN`.
- Alpine 3.24 / FRR 10.6.1-r0 and Debian Slim / FRR 10.3 package candidates each build, but their `mgmtd`, `zebra`, `ospfd` and `bgpd` fail `cap_set_proc` under a limited-capability profile without `SYS_ADMIN`.
- One **explicitly approved**, isolated Alpine-only diagnostic with `SYS_ADMIN` completed in 6 seconds. All four daemon launch calls returned 0 and were observed as FRR UID 100/GID 101 processes for a short period; `net.ipv4.ip_forward` read back 0 throughout; cleanup succeeded. The observed daemon `CapEff=0` is a snapshot, **not proof that a daemon cannot later regain a permitted capability**.

The proof is **startup feasibility**, not an integrated configuration, OSPF/BGP operation, functional necessity of SYS_ADMIN, Kubernetes admission, or absence of traffic forwarding.

## Proposed decision for Owner

Permit the existing project-built **Alpine 3.24 + distro FRR 10.6.1-r0 candidate** to proceed through Task 0001 with an **explicitly selected, lab-only capability profile that includes `CAP_SYS_ADMIN`**, **only if Owner accepts this ADR**. No claim of support for unrestricted production deployments.

This is an intentional risk acceptance for an owner-controlled lab environment, not a claim that ordinary route programming requires SYS_ADMIN. A project-maintained patched FRR or `--disable-capabilities` build is **not** the default just to avoid the daemon initialization request; it would introduce its own privilege-model and maintenance review.

The chart **must not silently add SYS_ADMIN**. Require an explicit operator/lab binding for the elevated profile, and fail template validation when it is absent while the selected packaged FRR runtime needs that profile. Avoid a complex profile-management framework: one documented positive selection and one reject-by-default validation gate suffice. Do not weaken or mutate cluster policy automatically.

### Shipped lab-Pod boundaries

- Keep `privileged: false`, `hostNetwork: false`, `hostPID: false`, `hostIPC: false`, no hostPath, no host container-runtime socket, and `automountServiceAccountToken: false`.
- Drop `ALL` capabilities and add back a **measured minimum** including `CAP_SYS_ADMIN` when this specific lab profile is explicitly opted in. The diagnostic's eight-capability set is **evidence**, not an automatic mandatory/recommended production set; drop unnecessary setup-only caps when valid.
- Explicit `seccompProfile: RuntimeDefault` and `allowPrivilegeEscalation: false` where the chosen FRR startup/drop-user behavior permits; do not silently override seccomp, privilege-escalation controls or host isolation if a runtime test fails.
- Bind to the already-approved two designated Worker nodes and a dedicated authorized lab namespace with least-privilege RBAC. **Do not label or relax the whole cluster's namespaces.**
- Kubernetes **Pod Security Standards Baseline and Restricted reject `SYS_ADMIN`** (and the expected NET_ADMIN/NET_RAW set). A namespace/cluster Admission exception, if necessary, is **a separate Owner-administered and audited infrastructure decision**. The chart must not create it.
- Preserve provenance (immutable base-image digest, FRR package version/revision, dependencies, built image digest). Maintain explicit security update/rebuild ownership.

### Unchanged hard RR non-transit guarantee

The RR is control-plane-only. Neither `SYS_ADMIN` nor `NET_ADMIN` permission changes the requirement that **packets must not transit between any RR interfaces**.

- Establish and read back `net.ipv4.ip_forward=0` inside the Pod network namespace **before** operating the routing service, and fail closed if it cannot be set/verified. Continuously check for drift at a bounded documented cadence; **readiness alone is insufficient** because it does not stop forwarding or running BGP.
- Do not assume setting `securityContext.sysctls: net.ipv4.ip_forward` will be accepted: it is **not** in Kubernetes' default **safe sysctl** list. Never change Worker host sysctls or kubelet unsafe-sysctl policy automatically to bypass this gate.
- Keep FRR OSPF `max-metric router-lsa administrative` and `bgp no-rib` (subject to reflection proof) as defense in depth, **not forwarding enforcement**.
- Integrated Kubernetes tests must explicitly verify startup, container restart, negative transit packets in normal and transit-VLAN-failure conditions, and stop/fail closed on forwarding drift. A user with kernel-capability access can still create residual compromise risk; no "absolute isolation" security claim is made.

## Gates and scope

1. **Owner acceptance gate:** This ADR and the corresponding Implementation Contract update must merge to `main` before Codex adds a SYS_ADMIN-enabled lab Pod/Helm template.
2. **Static/runtime gate:** Build the project-owned runtime; generate and validate 2 Pods, 2 ConfigMaps, 8 NADs; test integrated FRR config, expected daemon identities and capability masks, and Kubernetes policy/admission in the **actual approved lab**.
3. **Routing/non-transit gate:** Prove OSPFv2 P2P, iBGP reflection, shared Cluster ID, loopback NEXT_HOP behavior, `bgp no-rib` and negative transit packet behavior. Mark every unexecuted check NOT RUN.
4. **Operational/release gate:** Owner separately accepts any broader deployment support or change from this restricted lab boundary, plus formal image scan/SBOM and lifecycle/recovery acceptance.

If a workload demands `privileged`, host networking, altered FRR privilege handling, a blanket namespace policy exception or inability to preserve forwarding=0, **STOP** with reproducible evidence; do not invent alternate architecture.

## References

- [Task 0001 diagnostic](../tasks/0001-sysadmin-diagnostic.md) (in Draft PR #6 until merged)
- [Task 0001 runtime evaluation](../tasks/0001-runtime-evaluation.md) (in Draft PR #6 until merged)
- [Kubernetes Pod Security Standards](https://kubernetes.io/docs/concepts/security/pod-security-standards/)
- [Kubernetes sysctl safe/unsafe classification](https://kubernetes.io/docs/tasks/administer-cluster/sysctl-cluster/)
