# Home single-Client development topology

Scope authorization: [Issue #9 Owner correction](https://github.com/si32288564/frr-route-reflector/issues/9#issuecomment-6209398167).
Baseline: accepted main `885e5c97e308b2b1442c378927613b2383dc6408`.
This is a bounded development option, not a replacement for the original topology.

## Configuration contract

`topology: four-client` is the backward-compatible default: two distinct Workers,
four Clients, four links per RR, two Pods/two ConfigMaps/eight NADs.

Explicit `topology: home-single-client` requires exactly one Client, two independent
RR identities on **one** fixed Worker, and `net1` only per RR: two Pods/two
ConfigMaps/two distinct VLAN NADs and /31 pairs. Other cardinalities/mixed modes
are rejected. Both RRs share the ASN/Cluster ID/OSPF area but retain distinct
router IDs and loopbacks. Co-location is not Worker-level redundancy.

The single Helm values input owns routing and attachments. No arbitrary FRR
text or new environment-variable configuration authority is introduced. FRR
remains IPv4 iBGP RR, OSPFv2 P2P, `bgp no-rib`, permanent administrative max-metric,
unchanged NEXT_HOP, no RR-to-RR peer. The entrypoint accepts exactly one or four
declared sequential VLAN interfaces and rejects extras/missing interfaces before
FRR starts. Existing UID/capability/seccomp/forwarding/shutdown behavior is retained.

`examples/home-documentation-values.json` is an offline documentation fixture,
**not a deployable home network binding**. Actual values stay outside Git. The
old runtime's four-interface entrypoint cannot boot the new home topology; use
an image built from this change, not the old artifact with a misleading tag.

## Validation evidence — 2026-10-16 JST

Executed on the existing development build host (no new Docker test network):
Helm v3.19.0+g3d8990f, Python 3.14.4.

```sh
python3 tests/test_chart.py
docker buildx build --platform linux/amd64 --load --provenance=false \
  --tag frr-home-dev:single-client --file container/Dockerfile container
```

- PASS: original Helm lint/template/determinism, 2/2/8 mapping and 33 invalid inputs.
- PASS: home Helm lint/template/determinism, 2/2/2 mapping and 13 invalid inputs.
- PASS: original fixture render is byte-identical to accepted main; SHA256
  `3a732fc2af0007d5f85bb55c54df7654e31637625f79c2531b8ff43489438afb`.
- PASS: `git diff --check`, Bash syntax, Python test compilation.
- PASS: AMD64 build; manifest
  `sha256:2dd7e50583fcaea150559a7897e94868081800db6768c10e0f747558dfd3125f`,
  config `sha256:d4a8a6d9eb948dcc65dbe4d185007b1b623f93519772d197efedd8936d65f74a`.
  Existing pinned Alpine/FRR package layer was reused from cache. No image published.
- NOT RUN: FRR CLI config syntax, updated-container live startup/restart/guard
  tests, emulator execution, native AMD64 execution. Build is not execution proof.
  The existing `tests/test_container.py` now accepts `--home`; it was not run.

## Actual home deployment progression and limit

Only the Owner-designated home CP/Worker on the known hypervisor were targeted.
Worker VM definition reports x86_64 with an existing bridge-backed virtio NIC;
this is VM-management evidence, not a live guest CPU/CNI observation.
CP SSH attempts from local, the development host and the known hypervisor did
not establish a session. Guest-agent address queries reported agent not configured.
Private endpoint details and original results are retained outside Git.

BLOCKED: home CP/Worker management connectivity. No accessible home Kubernetes
API/config was established. No substitute company cluster was queried.
Home Calico, Multus/NAD, effective Admission, actual NIC/VLAN permission and
Client access remain NOT OBSERVED. Actual-values Helm rendering, containerd image
delivery, Pod deploy, OSPF Full, BGP Established, learned routes/kernel FIB,
forwarding readback and Pod recreation are **NOT RUN**. No host/CNI/policy/VM
change was made to bypass the access limitation; no new vNIC/network was created.

After access is restored, read this **home** cluster's current prerequisites;
bind one real Client/two VLAN /31 links; render the private home values. Assess
only any genuinely required shared CNI/Admission changes with target, impact and
rollback before mutation. Install one release and verify RR01 then RR02, including
unique identities, `ip_forward=0`, exact image/caps, FRR health and actual one-Client
OSPF/BGP/route acceptance. Stop/recreate one RR at a time using the existing bare
Pod cleanup/identity rules; no `helm --force` or guessed duplicate incarnation.

A single Client cannot demonstrate reflection to another Client, Client-to-Client
packet nontransit, or Worker-failure redundancy. Those are deliberately NOT RUN,
not acceptance PASS. Empty kernel FIB alone is not learned-route no-rib proof.
