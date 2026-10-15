# Task 0003 — AMD64 artifact qualification: builder STOP

Codexによる報告:

Date: 2026-10-15 JST. Authority: [Issue #10](https://github.com/si32288564/frr-route-reflector/issues/10),
accepted main `885e5c97e308b2b1442c378927613b2383dc6408`, and its governing
documents. Parent: [Issue #9](https://github.com/si32288564/frr-route-reflector/issues/9).

## Outcome

**BLOCKED / STOP at execution step 1: no accessible, authorized native AMD64
Docker builder was established.** No build or runtime qualification was attempted.
The authorized container-development host provides native ARM64 Docker. The
already authorized AMD64 lab host is reachable, but `docker` is not available
in the current authorized SSH environment. This does not prove that no Docker
installation exists anywhere on that host or elsewhere; it means no usable
authorized native AMD64 builder was established by these bounded checks.

No host provisioning, package installation, alternate-host access, cross-build
or emulation was attempted. The lab host's previous test-access authorization
is not treated as permission to install Docker or change its role.

## Executed read-only evidence

Private host identities and SSH targets are intentionally omitted. The labels
below identify roles, not real DNS names. SSH used `BatchMode=yes` and
`ConnectTimeout=10`; the AMD64 host was reached through the already authorized
development host. Both SSH command invocations returned 0. Only the following
read-only probes ran; the second probe captures lookup status explicitly.

Authorized container-development host:

```sh
uname -m
command -v docker
docker version --format '{{.Server.Arch}}'
```

```text
aarch64
/usr/bin/docker
arm64
```

Already authorized AMD64 lab host, initial probe:

```sh
uname -m
command -v docker
if command -v docker >/dev/null 2>&1; then
  docker version --format '{{.Server.Arch}}'
fi
```

```text
x86_64
```

Explicit lookup-status confirmation on the same AMD64 host:

```sh
uname -m
command -v docker
result=$?
printf 'docker_lookup_exit=%s\n' "$result"
if [ "$result" -ne 0 ]; then
  printf 'Docker CLI unavailable in current authorized SSH environment\n'
fi
```

```text
x86_64
docker_lookup_exit=1
Docker CLI unavailable in current authorized SSH environment
```

The local source-development machine also reported `arm64` from `uname -m`.
No Docker container was created, so container cleanup/absence validation is
**NOT RUN / not applicable**, not a runtime cleanup PASS.

## Per-platform comparison

ARM64 entries are historical results from the accepted
[Task 0001 evidence](0001-implementation-evidence.md), not tests rerun here.

| Verification | ARM64 accepted evidence | AMD64 Task 0003 |
|---|---|---|
| Usable native Docker builder | PASS, historical; ARM64 reconfirmed by server query | BLOCKED, native host reachable but Docker lookup exit 1 |
| Platform base manifest, exact signed packages/dependencies | PASS, historical ARM64 build/inventory; not AMD64 provenance | NOT RUN, stopped before step 2 |
| Image build, arch, ID/manifest, inventory and size | PASS, historical | NOT RUN |
| Helm lint/template/schema and 33 negative cases | PASS, historical | NOT RUN |
| Both generated FRR syntax checks | PASS, historical | NOT RUN |
| watchfrr/four daemons, integrated config, loopback/VLAN | PASS, historical isolated Docker fixture | NOT RUN |
| Seven-cap profile, capability masks, seccomp/NoNewPrivs | PASS, historical observed profile only | NOT RUN |
| Restart discards edits; normal stop/cleanup | PASS, historical | NOT RUN |
| Missing-interface refusal; namespace-local forwarding drift shutdown | PASS, historical | NOT RUN |
| Kubernetes/G-3 routing, NEXT_HOP and negative transit packets | NOT RUN | NOT RUN |

No AMD64 base digest, package availability, dependency versions, image size,
SBOM/CVE state, capability behavior or FRR functionality is asserted. ARM64
success cannot establish any of these for AMD64. There is no newly observed
FRR/package failure; the blocker is the execution prerequisite.

## Boundaries and next decision

Container, Chart, tests and all previous evidence are unchanged. No Kubernetes
API operations, deployments, image publication, host sysctl/network/CNI edits,
capability changes, or seccomp relaxation were performed. Parent G-3 remains
blocked on its separately approved environment bindings and prerequisites.

Owner decision needed: identify and authorize access to an **existing
nonproduction native AMD64 Docker builder** (including confirmation of its
suitability for the accepted disposable seven-cap Docker tests). Then resume
at step 2. Provisioning or installing a builder requires separate authorization;
it is not a fallback taken under this task. A separately approved cross-build
could provide build evidence only, not native runtime qualification.

The requested `codex/g3-amd64-qualification` conflicts with the existing local
`codex` branch's Git ref namespace. As explicitly permitted by Issue #10,
`codex-g3-amd64-qualification` was created from accepted main instead. The old
branch and history were preserved. This is a documentation-only STOP report,
not artifact acceptance. Issue #9/#10 remain open; no main merge is performed.
