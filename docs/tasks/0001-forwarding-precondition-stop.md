# Task 0001 — namespace forwarding startup precondition

Status: **BLOCKED for the observed default runtime**, not Container/Helm
completion. The previous capability STOP is resolved by accepted ADR 0011;
this record does not reopen that decision or repeat daemon capability diagnosis.

Authority: accepted main `4b9027e2b97a1ddd3378741ce79832a27db56624`
(PR #8) merged into codex preserving history. Owner's implementation-resume
instruction and ADR 0011 require namespace-local forwarding=0 before FRR starts,
fail-closed on inability to establish it, and no Worker/kubelet/admission changes.

## Measured fact

On the authorized container-development host, the existing ARM64 Alpine 3.24 /
FRR 10.6.1-r0 evaluation image was reused at recorded Docker identity
`sha256:cc34cc1b8b4d93d8834472085f7d53792ad28cd97416319808a0fc3c1cd4f9ca`.
No distro comparison or daemon capability diagnostic was repeated.

With network none, private default namespaces, default seccomp,
no-new-privileges, drop ALL and only the approved eight capabilities, default
namespace `net.ipv4.ip_forward` was **1**. `/proc/sys` was a separate **read-only**
proc mount. `sysctl -w net.ipv4.ip_forward=0` failed with:

```text
sysctl: error setting key 'net.ipv4.ip_forward': Read-only file system
```

The new `container/forwarding-gate.sh` attempts namespace-local disable only
when necessary, reads it back and fails on error. It makes no host fallback or
mount changes. The negative test recorded gate exit **1**, readback still **1**;
no routing process was started. This prevents unsafe activation but does not
establish a usable non-forwarding RR on the observed default runtime.

A separate positive-control container started by Docker with namespace-local
`--sysctl net.ipv4.ip_forward=0` recorded **0** before/after and gate exit **0**.
That runtime initialization is not a Worker sysctl change. It proves the gate
can accept a pre-initialized non-forwarding namespace, **not that Kubernetes
will admit or initialize the same setting**. The prior daemon startup diagnostic
also used this Docker initialization, so its success did not close this binding.

Executed reproduction on the container-development host:

```sh
sh /tmp/check-forwarding-precondition.sh /tmp/forwarding-gate.sh
```

Exact transferred scripts: `tests/check-forwarding-precondition.sh` and
`container/forwarding-gate.sh`. Captured output:
`docs/evidence/task0001-forwarding-precondition.txt`. The reproduction uses
disposable containers, launches no daemons, and changes no host sysctl or mount.
The harness exited 0 because the negative refusal and positive acceptance
matched their expectations. Do not interpret that as a completed runtime PASS.

The first exploratory inline check reproduced the same sysctl failure but its
trailing mount-output sed expression had a quoting error; it is not used as
mount evidence. The saved standalone test replaced it with an exact awk match.

## Limits and finite resolution

This is a measured Docker-runtime binding problem, **not proof that forwarding
cannot be disabled in every Kubernetes environment**, and not a finding that
NET_ADMIN/SYS_ADMIN are insufficient on a writable namespace-local proc mount.
No unsupported general conclusion about all CNI/container runtimes is intended.

The known Kubernetes control-plane management name resolved from the development
host, but an attempted read-only SSH connection timed out at banner exchange.
No Kubernetes admission, kubelet configuration or Pod network state was
observed. Private management names/addresses are intentionally omitted here.

Finite options for Chat/Owner to resolve the implementation precondition:

1. Confirm an existing authorized lab mechanism that initializes this Pod's
   network namespace with forwarding=0 (for example an already-admitted per-Pod
   runtime sysctl binding). Codex can then validate it without changing cluster
   policy. Do not assume the Kubernetes unsafe sysctl field is admitted.
2. Review a narrowly scoped container-local proc/mount mechanism if such a
   mechanism is desired. No remount/new proc mount, readonly-path bypass,
   unconfined seccomp or privileged operation was attempted or incorporated.
   A mount-related security-boundary change must be explicit rather than hidden
   inside the entrypoint.

Neither option requires a new routing architecture, FRR fork, controller or
capability framework. Merely documenting `forwarding must already be 0` without
an actual lab binding would leave the requested usable runtime gate unresolved.
An arbitrary Docker success with `--sysctl=0` must not mask that open obligation.

## Verification matrix

| Check | Result / meaning |
|---|---|
| Fetch and merge accepted ADR 0011 without rewriting history | PASS |
| Shell syntax and diff whitespace checks | PASS |
| Default runtime can disable namespace forwarding | FAIL, read-only sysctl, remains 1 |
| Gate rejects unsafe default before daemon activation | PASS |
| Gate accepts Docker-preinitialized forwarding=0 | PASS, Docker only |
| Production entrypoint, recurring drift shutdown, standard watchfrr startup | NOT RUN / not yet implemented |
| Final RR image build / FRR integrated config syntax | NOT RUN |
| Chart/schema/negative tests / 2 Pod + 2 CM + 8 NAD | NOT RUN / not yet implemented |
| Kubernetes admission, attachment, neighbor/reflection/packet/lifecycle tests | NOT RUN |
| Requested Task 0001 completion gate | BLOCKED pending namespace binding resolution |

Only the startup safety gate and its finite tests are added in this increment;
they are not presented as a completed CNF or full nonTransit enforcement.
Existing capability/STOP/diagnostic records remain unchanged. main was not
merged by Codex; Issue #5 remains open and PR #6 remains Draft.
