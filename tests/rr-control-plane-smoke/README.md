# RR smoke — measured startup slice; connected execution STOP

Codexによる報告:

2026-10-16 JST. [Issue #9 authority](https://github.com/si32288564/frr-route-reflector/issues/9#issuecomment-6195997779).
Accepted main `885e5c97e308b2b1442c378927613b2383dc6408`; new independent
branch, **only this directory changed**. PR #14/Issue #12 and accepted
Container/Helm/README/governance remain untouched.

```sh
python3 tests/rr-control-plane-smoke/test_fixture.py
timeout --signal=TERM --kill-after=15 165 python3 tests/rr-control-plane-smoke/startup.py --output /tmp/rr-startup.json
```

Native ARM64 existing G-2 image `sha256:7acfef1c1e4fdf06c2f5d15383073ba3a9c78c24a52beee8d85da04e8102d47a`;
FRR 10.6.1, Docker 29.1.3, Helm 3.19.0, Python 3.14.4/PyYAML 6.0.3.
Final run exited 0 in **2.539528s**, 2026-10-15 16:02:11–16:02:13 UTC.

| Actual observation | Result |
|---|---|
| 2 real bgpd processes concurrently healthy; exact per-RR Helm bytes | PASS short startup snapshot, not sustained routing |
| 2 generated Client configs, actual `vtysh -C -f` | PASS syntax only, no Client started |
| `bgp no-rib`, 4 peers retained, no RR-RR peer; RR forwarding readback 0 | PASS observed config/state, not behavioral proof |
| BGP/OSPF | 4 Idle peers and no OSPF neighbors each; live peering NOT RUN |
| Reflection, NEXT_HOP UPDATEs, ORIGINATOR_ID/CLUSTER_LIST | NOT RUN / connected execution BLOCKED |
| Learned service-route exclusion from RR kernel FIB | NOT RUN; baseline absence without learned routes is vacuous |
| Client FIB recursion / controlled packet non-transit / RR-loss routing | NOT RUN; no packet probe transmitted |
| Normal stop / exact-container cleanup and absence | PASS both final containers; earlier attempt also cleaned |

```text
Actual:    RR01 [dummy eth0 -> net1..4]  ||  RR02 [dummy eth0 -> net1..4]
           independent network-none namespaces; no cross-container link
Proposed:  RR01.eth0 --+-- RR02.eth0 --+-- C1.eth0 --+-- C2.eth0
                      one unique internal Docker tagged-L2 fabric
           C1<->RR01 VLAN1101; C2<->RR01 VLAN1102
           C1<->RR02 VLAN1105; C2<->RR02 VLAN1106
           C1<->C2 VLAN1200 /29 only; RRs never join it
```

[Exact addresses/interfaces/config derivation and limits](PLAN.md).
RR net3/4 and all four peer definitions stay unchanged; two Clients are only a
smoke subset, not the accepted G-3 topology. Client prefixes are locally
originated test routes, not proof of eBGP next-hop rewriting.

**STOP before creating a communication fabric.** Existing authorized G-2 uses
`network none`; connected Clients need a new Docker bridge/veth transport.
Co-locating all roles would conflate RR network namespaces/FIBs and conflicting
net1..4 identities. No existing shared network is presumed authorized.
Request **one Owner approval** for the exact bounded one-internal-bridge/four-
container setup in PLAN, with the unchanged seven-cap G-2 profile, no uplink,
ports, host mounts/namespace entry or policy relaxation, and exact owned-resource
cleanup. Docker bridge creation has host network effects; feasibility remains
unverified. `--connected` currently refuses exit 78 **before Docker**, with no
override that silently grants authority.

G-2-only execution retained default seccomp/no-new-privileges, 256 MiB memory+
swap and 128 PIDs per RR. bgpd UID/GID 100/101, NoNewPrivs=1/Seccomp=2; effective
capabilities 0 are sampled, not proof SYS_ADMIN cannot later be raised.
[Measured commands/configs/process/RIB/FIB/cleanup](measured-startup.json),
[earlier collector failure](first-attempt.json), [validation history](validation.txt).
Initial static IP-prefix comparison and Docker CAP_ representation assertions
were corrected, without changing permissions or config. Native AMD64 and G-3
remain NOT RUN. No network create, K8s, publish, scanner, rebuild or main merge.
