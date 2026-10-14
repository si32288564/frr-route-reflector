# Task 0001 — capability STOP evidence

Status: **BLOCKED**, not an implementation completion or acceptance claim.

Base: accepted `main` commit `2fa546d02c12c7be37579f432dd09388ced49195`.
Issue: https://github.com/si32288564/frr-route-reflector/issues/5

Read AGENTS.md, Project Governance, Requirements, Architecture, Network Design,
Implementation Contract, Acceptance Criteria, ADR 0001–0009 and task 0001.
The merged contract and Issue #5 satisfy the execution authorization precondition;
historical proposal labels in the documents do not undo that merge.

## Reproduction

Run `sh tests/reproduce-zebra-capabilities.sh` on a Linux Docker development host.
The disposable container has no external network, no host mount, no host network,
no privileged mode and no SYS_ADMIN. Only its own network namespace receives
`net.ipv4.ip_forward=0`. Runtime path ownership is prepared before daemon startup.

Candidate upstream input: `quay.io/frrouting/frr:10.3.1`, resolved by executed pull to
`sha256:f90d26a9fd5c14fc5795a73b4254ac88bc3186c45bbeb220a225fb6182de812c`.
This is a tested candidate, not an approved final base or project-built image.
Docker server: 29.1.3. Helm available: v3.19.0+g3d8990f.

The initial probe reported FRR `10.3.1_git`, forwarding `0`, and:

```text
privs_init: initial cap_set_proc failed: Operation not permitted
Wanted caps: cap_net_admin,cap_net_raw,cap_sys_admin=p
Have   caps: cap_chown,cap_setgid,cap_setuid,cap_net_admin,cap_net_raw=p
zebra_exit=1
```

An earlier probe omitted CHOWN and also failed ownership preparation. Adding
CHOWN did not remove the independent SYS_ADMIN capability failure. The script
additionally prepares writable disposable runtime directories to isolate that
failure from crash-log directory permissions. Mode 777 is confined to this
diagnostic container; it is not a proposed runtime policy.
FOWNER is used only to prepare these pre-existing diagnostic directories.
Final reproduction after directory preparation exited 1 with no directory
error, forwarding readback `0`, and the same wanted capabilities. Its exact
available-capability line was:

```text
Have   caps: cap_chown,cap_fowner,cap_setgid,cap_setuid,cap_net_admin,cap_net_raw=p
```

Local `sh -n tests/reproduce-zebra-capabilities.sh` and `git diff --check` passed.

## Boundary and finite alternatives

Task 0001 explicitly requires STOP if the selected FRR image requires broad
privilege such as SYS_ADMIN. Implementation Contract §4 and ADR 0007 prohibit
silently expanding that security boundary. No SYS_ADMIN trial was performed.
This blocks adoption of this candidate and implementation completion; it does
not establish that all FRR versions/builds require SYS_ADMIN.

Chat/Owner should decide whether to authorize evaluation of a different pinned
FRR distribution/build that avoids this capability request, or review a narrowly
specified security exception for this distribution. Prefer evaluating a build
without the unnecessary namespace capability; behavior still needs proof. No
privilege exception, custom FRR patch, controller or architecture revision is
implemented by this evidence PR.

## Verification status

| Check | Result | Evidence / limit |
|---|---|---|
| Latest accepted main and governing documents | PASS | Base above; read before changes |
| Upstream candidate pull/version | PASS | Digest and daemon version above |
| Disposable Docker namespace forwarding value | PASS | Readback `0`; not Kubernetes proof |
| Zebra startup without SYS_ADMIN | FAIL | Capability initialization failure, exit 1 |
| Container implementation / image build | BLOCKED | STOP before implementation |
| Helm lint/render/schema/negative tests | NOT RUN | Chart not implemented at STOP |
| FRR integrated config syntax | NOT RUN | No generated config exists |
| Kubernetes forwarding gate / loopback / daemon startup | NOT RUN | No deployment performed |
| OSPF/BGP/reflection/no-rib/NEXT_HOP/packet tests | NOT RUN | No integrated topology exercised |
| Replacement/recovery/rollback | NOT RUN | No operational readiness claim |

The KVM host is reachable and exposes virtual machines, but the attempted
management-name lookup for the control-plane VM failed. This is a lab-access
limitation, not the architecture STOP cause. No private hostnames, addresses or
raw environment inventory are included here. No cluster policy, host sysctl,
existing workload or VM was changed. The pulled candidate remains cached on the
development host; probe containers use `--rm`.
