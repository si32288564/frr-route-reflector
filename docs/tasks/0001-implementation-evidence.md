# Task 0001 — Container/Helm implementation evidence

Codexによる報告:

Authority: accepted main `4b9027e`, Issue #5 comment 6180703043 and PR #6
Architecture review 5526023836. Date: 2026-10-15 JST. This increment implements
the static/container gate; it does **not** complete Kubernetes or routing
acceptance. All previous STOP, runtime comparison and one-time diagnostic
records remain historical evidence and were not rerun as that diagnostic.

## Result and implementation

The project-owned image starts the generated integrated FRR configuration under
standard watchfrr, verifies four VLAN links and stable loopback, rejects unsafe
forwarding and detects drift with shutdown. The Chart renders exactly **2 bare
Pods + 2 per-RR ConfigMaps + 8 VLAN/static-IPAM NADs** from one strict values
input. Missing lab-sysadmin selection rejects render; no cluster prerequisite
or policy is installed. See [binding](../implementation-binding.md) and
[proposed, unvalidated lab runbook](../runbook.md).

New implementation files: `container/Dockerfile`, `container/entrypoint.sh`,
`container/frr-action.sh`, `container/health.sh`, `container/daemons`, revised
readback-only `container/forwarding-gate.sh`; Chart metadata/default values/
schema/helpers/resources under `charts/frr-route-reflector/`;
`examples/documentation-values.json`; `tests/test_chart.py`,
`tests/test_container.py`, `.gitignore`; README, binding/runbook and this evidence.
Historical gate evidence reflects the previous implementation at its original
commit; the current gate deliberately does not attempt a proc write.

## Final build identity and environment

- Official Alpine 3.24 base:
  `sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6`.
- Official Alpine FRR `10.6.1-r0`; daemon version `10.6.1`; tini `0.19.0-r3`.
- Final runtime manifest:
  `sha256:970672c57f33346f58362c22c30490d03d3918a45d7095fe602d178132c92d9f`.
- Docker image/index ID:
  `sha256:7acfef1c1e4fdf06c2f5d15383073ba3a9c78c24a52beee8d85da04e8102d47a`.
- Native ARM64/aarch64, Docker server 29.1.3; Helm v3.19.0+g3d8990f;
  Python 3.14.4, PyYAML 6.0.3.
- Docker inspect `.Size`: **13,620,747 bytes**, store-reported metric, not an
  uncompressed filesystem size or security score. APK reports 42.6 MiB/35 packages.
- Complete installed APK metadata: `docs/evidence/task0001-implementation-packages.txt`.
  No setpriv, libcap-utils, compiler or custom FRR build is in the final image.
  Distro FRR optional daemon binaries remain installed but disabled.

Version constraints and an immutable base do not guarantee repository retention
or bit-identical rebuilds. No registry publication or formal release occurred.

## Commands and executed evidence

Build and all Docker tests ran on the authorized container-development host.
Source was authored locally and transferred to a unique task directory. No
Kubernetes operations, deployment or environment modifications were performed
in this increment. The test fixtures synthesize eth0 and four VLAN interfaces
**inside a disposable network-none Docker namespace**, not a Worker trunk or
actual Multus attachment. Configuration is copied into the container, not mounted
from the host. Docker initializes its namespace with forwarding=0 as a stand-in
for Calico's already-reviewed initializer; this is not a Kubernetes proof.

```sh
docker build -t frr-task0001:implementation container
helm lint charts/frr-route-reflector -f examples/documentation-values.json
python3 tests/test_chart.py
timeout 90 python3 -u tests/test_container.py
timeout 90 python3 -u tests/test_container.py --drift
timeout 90 python3 -u tests/test_container.py --missing-interface
sh tests/check-forwarding-precondition.sh container/forwarding-gate.sh
```

`test_chart.py` invokes helm template/schema/lint with temporary values, checks
determinism, exact resource counts, each 2×4 NAD/annotation/FRR/address mapping,
capabilities/namespace isolation and documentation-only sample IPs. Final run
rejects **33** negative cases. The preceding full suite had 32; a final DNS-name
constraint and corresponding negative test were added and rerun separately.

Each final container test returned 0 (test harness success), with forced removal
exit 0 and exact-name absence confirmed. Normal stop returns container exit 0;
the deliberately injected drift and missing-interface containers exit 1 as
expected. Restart overwrites a deliberately changed runtime frr.conf with exact
accepted ConfigMap bytes and still reads forwarding=0.

Inside the running container, the executed FRR syntax command was:

```text
vtysh -C -f /etc/frr/frr.conf
syntax_exit=0
rr-rr01 syntax_exit=0 output=''
rr-rr02 syntax_exit=0 output=''
```

Both generated ConfigMaps were separately copied to a readable temporary file
and checked by the installed version's `vtysh -C -f`. `vtysh -b` also applied
the desired boot bytes, and show running-config verified all four clients,
loopback-sourced neighbors, cluster ID, no-rib and max-metric. Show ip ospf
reported five interfaces and permanent administrative stub/max-distance LSA,
**zero Full neighbors**. BGP summary reported **four Idle peers**, no external
routes. These are intentionally unconnected fixtures, not routing failures or
Established claims.

Raw final build/static/runtime/CLI/capability/cleanup output is in
`docs/evidence/task0001-implementation-tests.txt`; the last 33-case/gate/absence
run is in `docs/evidence/task0001-implementation-static.txt`. Paths contain
documentation values and generated container IDs only, not private lab bindings.
Individual `bash -n` checks of all five runtime shell/config files returned 0;
`git diff --check` passed. An initial combined remote shell-syntax inventory
command had a quoting failure and was replaced by these individual checks;
the failed command is not counted as validation success.

## Security profile and safety scope

Drop ALL, add **CHOWN, SETUID, SETGID, NET_ADMIN, NET_RAW, NET_BIND_SERVICE,
SYS_ADMIN**; supplemental frrvty group 102. Root entrypoint/watchfrr UID 0,
protocol daemons UID 100/GID 101. Parent CapPrm/CapEff/CapBnd are `2034c1`;
daemon permitted masks `203000` (zebra) / `203400` (others), effective mask 0 at
observed snapshots. NoNewPrivs 1, Seccomp 2. Ambient/inheritable zero. The
effective-zero snapshots do not establish that SYS_ADMIN is never raised.
No FOWNER, CAP_KILL, privileged mode, host network/PID/IPC, hostPath or SA token.
RuntimeDefault seccomp and allowPrivilegeEscalation=false are explicit in render;
no-new-privileges/default seccomp were maintained in Docker testing. The default
seccomp conditional allowlist is not asserted unchanged by SYS_ADMIN.

CHOWN is setup ownership, SETUID/SETGID serve standard FRR drop-user and su stop.
FRR's four kernel capabilities are its measured initializer requirements. A
non-root launch was tried but ospfd checks EUID 0 before FRR privilege setup;
no source patch/disabled-capabilities workaround was used. Socket access was
resolved with the standard frrvty group, not added DAC capabilities. A seven-cap
working profile was validated; global minimality/functional SYS_ADMIN necessity
is not claimed. Earlier failing implementation attempts (non-root ospfd,
missing frrvty group, wrong global no-rib placement, temporary-file permissions)
were corrected and their final paths rerun; they are not hidden PASS results.

The wrapper reads forwarding at startup and at a nominal one-second normal
cadence; on violation it removes the boot marker, terminates watchfrr, invokes
standard frr-account stops, and exits nonzero. Drift was injected only by
host-side nsenter targeting the test container's network namespace, then the
test observed container exit 1. The host's network sysctl was never changed.
This verifies detection/shutdown, not zero-window non-forwarding or actual
packets. Real packet, attachment, restart and failure acceptance remains open.

Observed residual messages: mgmtd initially probes missing legacy daemon config
files before integrated vtysh application; no independent configs are maintained.
Zebra reports unsupported MPLS and a PTM PID-registration shutdown diagnostic.
These did not prevent successful integrated application or clean container exit;
logs are preserved. The image is not declared production-ready.

## Independent acceptance gates

| Validation | Result |
|---|---|
| ARM64 final image build and package provenance inventory | PASS |
| Runtime shell syntax and diff checks | PASS |
| Helm lint/template/schema, determinism, exact 2/2/8 and pairwise mapping | PASS |
| Invalid/unsafe values rejection | PASS, 33 cases |
| FRR syntax, both generated configurations | PASS, empty dry-run output, exit 0 |
| watchfrr/4 daemon startup, loopback, exact integrated bytes | PASS, isolated Docker fixture |
| Normal stop/cleanup, restart discards runtime edit | PASS, Docker only |
| Startup forwarding refusal, missing VLAN interface refusal | PASS |
| Sampled forwarding=0 and detector shutdown on injected drift | PASS, no packet claim |
| Actual Kubernetes admission/Multus/Pod startup | NOT RUN / deployment unauthorized |
| OSPF Full, BGP Established, route reflection/NEXT_HOP, no-rib with learned routes | NOT RUN |
| Negative transit packets, Client Transit failure, real Pod/Worker lifecycle/rollback | NOT RUN |
| Formal SBOM/vulnerability scan and release/license/security maintenance acceptance | NOT RUN / release gate |

**Container/Helm implementation gate:** implemented with the executed evidence
above, awaiting Chat/Owner review. **RR lab integration gate:** remains BLOCKED
on Owner-designated Workers/namespace, authorized admission and missing
Multus/NAD provisioning. The proposed runbook is not lab-validated. Issue #5
stays Open; PR #6 stays Draft; no main merge or accepted-state claim.
