# Task 0001 — ADR 0010 runtime evaluation

State: **BLOCKED at C-2**, requesting a scoped diagnostic security decision.
This adds new evidence; `0001-validation-stop.md` and the original upstream
10.3.1 reproduction remain unchanged and valid for their candidate.
Authority: merged main `376567f` (PR #7), ADR 0010 and Owner's resume instruction.
Main was merged into `codex` without rewriting either history.

## Executed candidate builds

Both builds ran on the authorized container development host, Docker 29.1.3,
native Linux `aarch64` / Docker `arm64`. No image was published.

| Input/result | Alpine first candidate | Single Debian alternative |
|---|---|---|
| Base | Official Alpine 3.24 | Official Debian trixie-slim |
| Base digest | `sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6` | `sha256:a29215f6a35e51e22adffa17f89e9d2ef06214e64a2bad10d765c46aea49f11f` |
| FRR package | `10.6.1-r0`, v3.24/community | `10.3-3+deb13u1`, trixie/main and trixie-security/main |
| Daemon version | `10.6.1` | `10.3` |
| Built index/image identifier reported by Docker | `sha256:cc34cc1b8b4d93d8834472085f7d53792ad28cd97416319808a0fc3c1cd4f9ca` | `sha256:e16ef278fd4184e0f3126ec15d70f09d0660c7e218aa83f98eaa5f1f8f5d505f` |
| Runtime manifest digest from build | `sha256:6bab359ba753b4d9a43c009d691e2d96478285a917fde1beab456c889d3e1fc9` | `sha256:ecf54f3ad19e4361a4c9ace47739dfac2fa09e79b562ff24568eaddaeb61baae` |
| Docker inspect `.Size` bytes | 13607333 | 49109364 |

Sizes are the values reported by this Docker image store, not a comparable
uncompressed filesystem measurement or a security score. APK reported 42.5 MiB
in 34 installed packages. Actual inventories are in `docs/evidence/` alongside
the exact final startup output. APK signature checks and APT signed-index checks
were enabled; no untrusted/unauthenticated installation switch was used.
These mutable repositories do not guarantee retention or bit-identical rebuilds.

Build recipes are `container/Dockerfile.{alpine,debian}-evaluation`. They are
evaluation shells, **not finished RR CNF containers**. To build without a host
directory context:

```sh
docker build -t frr-task0001:alpine-evaluation - < container/Dockerfile.alpine-evaluation
docker build -t frr-task0001:debian-evaluation - < container/Dockerfile.debian-evaluation
sh tests/evaluate-packaged-frr.sh frr-task0001:alpine-evaluation
sh tests/evaluate-packaged-frr.sh frr-task0001:debian-evaluation
```

The first executed Alpine build used `-f /tmp/Dockerfile.alpine-evaluation /tmp`;
its Dockerfile has no COPY/ADD and BuildKit did not report a filesystem-context
transfer. Debian used the stdin/no-directory-context recipe above.

## Runtime/capability observations

Each final probe used root UID/GID 0, `cap-drop ALL`, and exactly CHOWN, FOWNER,
SETUID, SETGID, NET_BIND_SERVICE, NET_ADMIN, NET_RAW. CHOWN/FOWNER and mode 777
prepare **disposable diagnostic directories**, not proposed production permissions.
Alpine's configured FRR account is UID 100/GID 101 (`frr`), supplemental frrvty
GID 102. No healthy steady-state daemon identity was established.

Observed parent permitted/effective/bounding mask: `00000000000034c9`;
inheritable/ambient zero; `NoNewPrivs: 1`, `Seccomp: 2`, one filter (Docker default,
no unconfined override). Both before/after forwarding readbacks were `0`.
These are Docker namespace observations, **not Kubernetes admission proof**.

| Daemon | Alpine exit | Debian exit | Requested permitted capabilities |
|---|---|---|---|
| zebra | 1 | 1 | NET_ADMIN, NET_RAW, SYS_ADMIN |
| ospfd | 1 | 1 | NET_BIND_SERVICE, NET_ADMIN, NET_RAW, SYS_ADMIN |
| bgpd | 1 | 1 | NET_BIND_SERVICE, NET_ADMIN, NET_RAW, SYS_ADMIN |
| mgmtd | 1 | 1 | NET_BIND_SERVICE, NET_ADMIN, NET_RAW, SYS_ADMIN |

All report `privs_init: initial cap_set_proc failed: Operation not permitted`.
An initial Alpine probe without NET_BIND_SERVICE also failed; adding it isolated
SYS_ADMIN as the remaining missing requested capability. This is a bounded
diagnostic profile, not a successfully minimized runtime profile. `watchfrr
--version` ran on Alpine; supervisor startup/config loading was NOT RUN because
the daemon gate failed. Installed files include standard frrinit/watchfrr,
vtysh, mgmtd and optional daemon binaries. No optional daemons or build tools
were manually launched. Debian dependencies include cron/systemd/logrotate;
their presence is not a claim that those services ran.

## Cause and evidence limits

Upstream [10.6.1 zebra/main.c](https://github.com/FRRouting/frr/blob/frr-10.6.1/zebra/main.c)
declares ZCAP_SYS_ADMIN in the startup capability array. The standard
[privs.c initializer](https://github.com/FRRouting/frr/blob/frr-10.6.1/lib/privs.c)
maps that to Linux CAP_SYS_ADMIN and applies the requested permitted set with
cap_set_proc before normal operation. This corroborates the measured startup
error. No source was patched and no capability handling was disabled.

**What is proven:** these packaged binaries request SYS_ADMIN during privilege
initialization even with no VRF/netns routing configuration supplied.
**What is not proven:** that OSPF, BGP reflection or ordinary kernel route
operations in one namespace actually need to exercise SYS_ADMIN. No trace of
successful runtime kernel operations exists because initialization failed.

## Proposed finite diagnostic — NOT AUTHORIZED / NOT RUN

Request authorization for one disposable **Alpine** diagnostic with SYS_ADMIN
added to the existing profile, using the recorded built runtime manifest. Its
purpose is to cross the initialization gate and observe daemon startup,
standard integrated config loading, stable loopback and the namespace-local
forwarding state; it does not authorize Kubernetes or a release permission.

Boundaries: `--network none`, private PID/IPC/net namespaces, no host mounts,
devices or Docker socket, no privileged/host-network flags, Docker default
seccomp retained, no-new-privileges, bounded memory/PIDs and a 60-second external
timeout. No host sysctl, cluster policy or existing workloads change. Only the
container namespace starts with ip_forward=0; verify before and after and abort
on drift. Test data uses documentation addresses only. Remove the container on
normal exit and timeout. No additional seccomp relaxation is implied by approval.

Residual risk: SYS_ADMIN is broad and Docker shares the host kernel; isolation
and seccomp reduce but do not eliminate kernel attack surface. Docker's default
seccomp policy may admit additional syscalls when this capability is added. A
disposable VM on the authorized KVM test host is the stronger isolation option
if Owner prefers it; no host-level privilege workaround will be substituted.

Finite choices: authorize this diagnostic (prefer disposable-VM isolation when
available), or keep the task blocked pending an approved packaged-runtime policy.
No random additional distro/tag sweep, patched FRR or disabled privileges is
proposed. Any shipped SYS_ADMIN grant remains a separate Owner decision.

## Verification matrix

| Check | Result |
|---|---|
| Preserve history and merge accepted ADR 0010 | PASS |
| Actual arm64 package availability, two candidate builds | PASS |
| Full installed package inventories and exact daemon failures | PASS (evidence collection) |
| Limited-capability daemon startup | FAIL, four exits 1 for each candidate |
| Docker namespace forwarding readback | PASS, 0 before/after; not a full safety guard |
| Runtime adoption gate / complete CNF | BLOCKED |
| SYS_ADMIN diagnostic / runtime operation tracing | NOT RUN, requires scoped authorization |
| Formal SPDX/CycloneDX SBOM and vulnerability scan | NOT RUN; syft/trivy/grype not found on development host |
| Helm/chart/schema/negative tests, integrated config syntax | NOT RUN, awaiting runtime gate |
| OSPF/BGP/no-rib reflection/NEXT_HOP, Kubernetes, packet tests | NOT RUN |
| Replacement/rollback | NOT RUN |

The APK installed database and dpkg-query inventory are provenance evidence,
not a formal SBOM or a clean-CVE assertion. Alpine community maintenance has a
different window from main; a final accepted runtime must define security
update/rebuild tracking rather than infer FRR support from a base release date.
Old evidence remains intact. No host/cluster security policy was weakened and
no SYS_ADMIN test was executed. Evaluation images remain only in the authorized
development host cache, and the test containers used `--rm`.
