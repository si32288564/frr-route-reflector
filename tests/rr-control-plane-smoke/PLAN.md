# RR control-plane smoke — fixture instructions and exact proposed setup

Codexによる報告:

2026-10-16 JST. Authority: [Issue #9 instruction 6195997779](https://github.com/si32288564/frr-route-reflector/issues/9#issuecomment-6195997779).
Base: accepted main `885e5c97e308b2b1442c378927613b2383dc6408`.
Only this fixture directory changes; PR #14/Issue #12, Container/Helm and shared
docs are untouched. This is **not** a completed route-reflection test or G-3.

## Run / measured result

On existing Workbox with existing Helm/PyYAML/Docker and the pinned G-2 image:

```sh
python3 tests/rr-control-plane-smoke/test_fixture.py
timeout --signal=TERM --kill-after=15 165 python3 tests/rr-control-plane-smoke/startup.py --output /tmp/rr-startup.json
# Always refuses before Docker; approval is not implied by a CLI switch:
python3 tests/rr-control-plane-smoke/startup.py --connected --output /tmp/not-created.json
```

Static fixture tests PASS. Final startup command exited 0, **2.539528 seconds**
(`2026-10-15T16:02:11.001932`–`16:02:13.541460` UTC). Both RR processes were
simultaneously healthy before sampling, then stopped normally and deleted.
This is a short startup snapshot, not sustained peer or forwarding acceptance.
[Actual output](measured-startup.json), [first failed collector attempt](first-attempt.json),
[validation chronology](validation.txt). FRR 10.6.1, native ARM64, Docker 29.1.3,
Helm v3.19.0+g3d8990f, existing Python 3.14.4/PyYAML 6.0.3. Exact existing image
ID: `sha256:7acfef1c1e4fdf06c2f5d15383073ba3a9c78c24a52beee8d85da04e8102d47a`.

| Observation | Result / boundary |
|---|---|
| Two native RR bgpd processes, unmodified Helm ConfigMap bytes | PASS startup/config hashes; all 4 peers per RR retained |
| Two Client configs through actual `vtysh -C -f` | PASS syntax only; Clients **not started** |
| Effective `bgp no-rib`, max-metric, no RR-RR peer | PASS observed config; no learned route behavior claimed |
| RR netns `ip_forward=0` | PASS sampled state, not packet proof |
| BGP / OSPF adjacency | 4 Idle peers and no OSPF neighbors each; live peering NOT RUN |
| Reflection / UPDATE NEXT_HOP / ORIGINATOR_ID / CLUSTER_LIST | NOT RUN / connected execution BLOCKED |
| Learned BGP route absent from RR kernel FIB | NOT RUN; baseline absent test prefixes is vacuous |
| Client FIB recursion / controlled negative transit packets | NOT RUN, no probe transmitted |
| One-RR loss/restart with surviving route reflection | NOT RUN; normal unconnected stops are not that test |
| Exact container cleanup | PASS, both final removals 0 / absence inspect 1; first-attempt containers also removed |

G-2 controls: two **independent network-none netns**, dummy eth0 and four VLANs
created only inside each; 256 MiB memory+swap/128 PIDs per RR, no host mounts,
devices or shared host namespaces, drop ALL plus the existing seven-cap lab
profile, no-new-privileges/default seccomp. Observed bgpd UID 100/GID 101,
NoNewPrivs 1/Seccomp 2, CapPrm `203400`, CapEff 0, CapBnd `2034c1`. Effective
zero is a sample, not proof permitted SYS_ADMIN cannot be raised. Timeout
termination itself was NOT fault-injected. No network create/connect or host
namespace entry was executed.

## Minimal exact connected fixture proposed — NOT AUTHORIZED / NOT CREATED

`fixture.py` derives all RR bytes and links from accepted Helm/example values;
it also generates two test Client configs and the exact interface map. Clients
3/4 remain defined on both RRs but absent from this smoke subset. Controlled
prefixes `.200/32` and `.201/32` in `198.51.100.0/24` would be local Client
loopback addresses, **not an eBGP Test-peer proof**. No static underlay is called OSPF.

```text
Now:       RR01 [dummy eth0 -> net1..4]     RR02 [dummy eth0 -> net1..4]
           no shared link, no Client process, no packets between namespaces

Proposed:  one unique Docker --internal tagged-L2 bridge, no physical uplink
           RR01.eth0   RR02.eth0   Client1.eth0   Client2.eth0
               |          |            |             |
           [all VLAN children below are in the owning container netns]
```

| Segment | RR side /31 | Client side /31 | Proposed VLAN |
|---|---|---|---:|
| RR01.net1 ↔ C1.net1 | 198.51.100.0 | 198.51.100.1 | 1101 |
| RR01.net2 ↔ C2.net1 | 198.51.100.2 | 198.51.100.3 | 1102 |
| RR02.net1 ↔ C1.net2 | 198.51.100.8 | 198.51.100.9 | 1105 |
| RR02.net2 ↔ C2.net2 | 198.51.100.10 | 198.51.100.11 | 1106 |
| Client-only C1.net3 ↔ C2.net3 | 203.0.113.17/29 | 203.0.113.18/29 | 1200 |

RR net3/4 retain 1103/1104 and 1107/1108 with their unchanged /31s, no Client
3/4 endpoints. Client net4 pads the existing four-VLAN entrypoint with an
unconnected 1201 (`203.0.113.32/31`) / 1202 (`203.0.113.34/31`), no OSPF.
RRs never join VLAN 1200. Loopbacks: RR `.1/.2`, Clients `.11/.12` in 192.0.2/24;
ASN 64512, Cluster ID 192.0.2.254. These are test documentation values only.

**Single minimal Owner decision:** authorize one task-owned internal Docker
bridge + four task-owned G-2-image containers, with the same per-container
profile/limits, at most 180s total and exact-ID/label cleanup. Proposed internal
management IPAM `192.0.2.224/28` (only after overlap preflight), bridge option
`com.docker.network.bridge.inhibit_ipv4=true`, masquerading disabled, no published
ports/uplink/default route. This deliberately needs approval: Docker creates
host bridge/veth and can manage host firewall rules; `--internal` is not a claim
of zero host impact or absolute isolation. See [Docker bridge behavior](https://docs.docker.com/engine/network/drivers/bridge/).
Tag transport/driver feasibility is **unverified**; no fallback host veth,
additional capability, remount, external VLAN, install or policy relaxation is
authorized. If it cannot work as bounded, STOP rather than improvise.

After approval, the first connected increment must collect actual Client→RR
and RR→Client UPDATE attributes (not just config/advertised intent), both RIBs
and RR kernel routes with a learned prefix, actual OSPF/Client FIB recursion,
and a controlled negative probe with sufficient ingress/egress evidence. If
existing instrumentation cannot prove a layer, leave that layer NOT RUN; do
not install tools/enter host namespaces without authority. Then isolate one
RR loss/restart and observe the surviving reflector. These phases are **not
implemented as an enabled connected runner** in this PR: `--connected` fails
closed before Docker. The runnable part today is rendering/static validation
and the already-approved G-2 startup slice.

No Kubernetes/Multus/PSA change, native AMD64 claim, Docker Hub/GitHub Release,
scanner, image rebuild or main merge. Return this measured slice for review,
then wait before creating the required new communication fabric.
