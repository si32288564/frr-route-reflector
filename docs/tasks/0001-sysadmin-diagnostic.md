# Task 0001 — one authorized SYS_ADMIN diagnostic

Completed once, 2026-10-15 JST (raw daemon timestamps are UTC).
Authorization: [Chat/Owner scoped review](https://github.com/si32288564/frr-route-reflector/pull/6#issuecomment-6180314494)
and Owner's explicit execution instruction. This is additional evidence, not a
replacement for the previous no-SYS_ADMIN failures.

## Identity and execution

Only the existing Alpine 3.24 / FRR 10.6.1-r0 ARM64 evaluation image was used:
Docker identity `sha256:cc34cc1b8b4d93d8834472085f7d53792ad28cd97416319808a0fc3c1cd4f9ca`;
runtime manifest previously recorded as
`sha256:6bab359ba753b4d9a43c009d691e2d96478285a917fde1beab456c889d3e1fc9`.
Before execution, Docker image inspection matched the recorded ID and arm64.
Docker server 29.1.3. No rebuild or Debian capability test was performed.

Executed on the authorized container-development host:
`sh /tmp/frr-task0001-sysadmin-once.sh`, an exact transferred copy of
`tests/diagnose-alpine-sys-admin-once.sh`. The script is retained for audit;
**do not rerun without a fresh authorization**. Exact conditions/commands and
output are in the script and `docs/evidence/task0001-alpine-sysadmin-diagnostic.txt`.

The unique container name was checked absent before creation. The container was
created stopped, then started under host-side `timeout -s KILL 55`. This reserved
time for forced cleanup within the approved 60-second execution bound. Actual
total elapsed time including removal was **6 seconds**; diagnostic/container/
script exit codes were all **0**, OOM false. Timeout did not fire.

Inspect recorded network none, private IPC, default private PID, no binds,
volumes-from, host devices or port publications; privileged false. Memory and
swap ceiling 256 MiB, 64 PIDs. Only CHOWN, FOWNER, SETUID, SETGID,
NET_BIND_SERVICE, NET_ADMIN, NET_RAW, SYS_ADMIN were added after dropping ALL.
Host sysctls and cluster/workloads were not changed. Runtime directory mode 777
is diagnostic preparation only, not a production permission proposal.

Host/container network, PID and IPC namespace inode values differed. Container
mount namespace was recorded; user namespace was the default (no user-namespace
remapping protection is claimed). Root UID/GID 0 launched the commands. Parent
CapPrm/CapEff/CapBnd were `00000000002034c9`; ambient/inheritable zero.
NoNewPrivs 1 and Seccomp 2 with one filter were observed in parent and daemons.
Docker default seccomp was retained without overrides; this does **not** mean
its effective syscall allowlist was unchanged after adding SYS_ADMIN.

## Daemons and observed permissions

Each command was `/usr/lib/frr/<daemon> -d --log stdout`, with management backend
started first, followed by zebra, ospfd and bgpd. No external peers or routing
configuration were added. The packaged default files were left in place.

| Daemon | Launch exit | Process after three 1-second waits | CapPrm | CapEff at snapshot | Stop observation |
|---|---|---|---|---|---|
| mgmtd | 0 | sleeping, UID 100/GID 101 | `203400` | 0 | Terminating on signal |
| zebra | 0 | sleeping, UID 100/GID 101 | `203000` | 0 | Terminating on signal; Zebra final shutdown |
| ospfd | 0 | sleeping, UID 100/GID 101 | `203400` | 0 | Terminating on signal |
| bgpd | 0 | sleeping, UID 100/GID 101 | `203400` | 0 | Terminating on signal |

All retained bounding mask `2034c9`, zero ambient/inheritable. `203000` decodes
to NET_ADMIN, NET_RAW, SYS_ADMIN; `203400` additionally includes
NET_BIND_SERVICE. Effective-zero snapshots show lowered privileges at those
instants; they do not prove that SYS_ADMIN was never raised between snapshots.
No initial cap_set_proc failure appeared with the approved added capability.

Signals were sent as the frr account using `su` rather than adding CAP_KILL.
After the two-second termination wait, the process scan found no remaining
named target daemons. The daemonized children's individual final exit statuses
were not available to the wrapper; launch return codes and termination logs
are the evidence, not invented child wait statuses.

Additional messages, preserved verbatim in raw evidence:

- mgmtd could not open zebra/ripd/ripngd/staticd/mgmtd daemon configuration
  files, then logged completion of reading config files and backend registration.
  No rip/static daemons were started by this test. A complete integrated boot
  configuration was not loaded or validated here.
- zebra disabled MPLS because kernel support was unavailable. MPLS is outside
  the RR task. At shutdown it also logged a PTM process PID registration error.
- bgpd announced listening on port 179 inside the isolated namespace only.

These observations do not justify declaring the complete FRR runtime healthy.
They identify startup/configuration issues for future reviewed implementation.

## Forwarding and cleanup

Readbacks before startup, after each daemon launch, each of three in-flight
samples and immediately before container exit were all **0**. No forwarding
drift was observed. This finite sampling is not a continuous enforcement proof
or a client-to-client packet test. Docker supplied the namespace-local sysctl;
host sysctls were not touched.

The EXIT trap invoked bounded `docker rm -f` for the unique container only:
cleanup exit **0**, then an exact-name query confirmed `container_absent=PASS`.
The container had already exited with running=false; forced removal removed
the diagnostic container and its private writable state. No other container was
targeted. Historical evaluation images and old evidence were retained.

## Results and next boundary

| Check | Result / limit |
|---|---|
| One authorized Alpine diagnostic within 60 seconds | PASS, one run, 6 seconds |
| Capability initialization and finite daemon process persistence | PASS for four tested daemon commands |
| Complete integrated runtime/config correctness | NOT RUN; missing config errors observed |
| Sampled namespace forwarding state | PASS, all 0 |
| SIGTERM behavior and complete container deletion | PASS, logs and absent-container check |
| Timeout/error-path cleanup fault injection | NOT RUN; code inspected, no second diagnostic authorized |
| Need for additional capabilities | None requested in this run |
| Functional necessity/use of SYS_ADMIN for normal routing | NOT RUN / not established; no syscall trace or traffic |
| External OSPF/BGP, no-rib reflection, packet forwarding | NOT RUN |
| Kubernetes admission, shipped capability contract, CNF/Helm implementation | BLOCKED pending Chat/Owner review |

The no-SYS_ADMIN failure and this added-SYS_ADMIN startup establish an
initialization gate for this packaged build. They do not establish functional
SYS_ADMIN necessity for ordinary RR routing. Shared host kernel exposure remains
despite namespaces/default seccomp and short duration. This used the authorized
development host, not a newly provisioned disposable VM; no VM-isolation claim
is made. No source patch, privilege-manager bypass or seccomp relaxation was
used. No SYS_ADMIN permission was added to a Pod or Chart.

The diagnostic is finished. Chat/Owner must review whether and under what
separate security contract subsequent runtime implementation may proceed.
No additional implementation or diagnostic run is authorized by these results.
