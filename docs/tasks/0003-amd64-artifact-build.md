# Task 0003 — Workbox multi-platform artifact-build follow-up

Codexによる報告:

Date: 2026-10-15 JST. Authority: [Owner clarification / Chat instruction](https://github.com/si32288564/frr-route-reflector/issues/10#issuecomment-6183718281).
Accepted main remains `885e5c97e308b2b1442c378927613b2383dc6408`.
The archived source was task commit `1df17efc00c4d2e93ea5aa90d3606cbdce488299`;
its container, Chart and tests are unchanged from accepted main.
The [earlier STOP](0003-amd64-qualification.md) is historical, not deleted.

## Four independent statuses

| Gate | Result | Scope |
|---|---|---|
| Workbox AMD64 artifact build | PASS | Existing cross-platform builder, local-only output; not native execution |
| Platform inspection and architecture-independent static tests | PASS | ELF/APK metadata; Helm lint/template/schema, determinism, 2/2/8 mapping and 33 negatives |
| AMD64 EMULATED Docker smoke test | NOT RUN | Working isolated host emulation runtime was not established; no setup attempted |
| Native AMD64 FRR runtime qualification | BLOCKED / NOT RUN | No Owner-authorized native AMD64 execution environment established |

No claim of FRR startup, working AMD64 privilege drop, daemon capability masks,
FRR syntax execution, restart/stop/drift behavior, routing, non-transit packets
or Kubernetes acceptance follows from these build/static results.

## Existing builder and exact build commands

Non-invasive probes: `uname -m`, `docker version --format
'client={{.Client.Version}} server={{.Server.Version}} arch={{.Server.Arch}}'`,
`docker buildx version`, `docker buildx ls`.

```text
aarch64
client=29.1.3 server=29.1.3 arch=arm64
github.com/docker/buildx 0.30.1 0.30.1-0ubuntu1
mybuild*: docker-container, running, BuildKit v0.32.2, linux/amd64,linux/arm64
default: docker, running, BuildKit v0.26.2, linux/arm64
```

Existing builder `mybuild` was used without creation/bootstrap/configuration
changes. No kernel handler/QEMU installation, service restart or privileged
builder creation was performed. BuildKit can execute the AMD64 Dockerfile RUN;
that does not establish a corresponding Docker-host emulation runtime. The
precise build-time emulation implementation was not independently identified.

Source was transferred with `git archive HEAD container charts examples tests`
to a unique private temporary task directory. From that directory:

```sh
timeout 180 docker buildx build --builder mybuild --platform linux/amd64 --no-cache --progress plain --load --metadata-file amd64-metadata.json -t frr-task0003:amd64 container
timeout 180 docker buildx build --builder mybuild --platform linux/arm64 --no-cache --progress plain --load --metadata-file arm64-metadata.json -t frr-task0003:arm64 container
```

Both commands exited 0. Each exported one platform-specific OCI image manifest,
then imported it locally; no multi-platform output index or registry publication
was created. [AMD64 log](../evidence/task0003-amd64-build.txt),
[ARM64 log](../evidence/task0003-arm64-build.txt), and
[AMD64](../evidence/task0003-amd64-metadata.json) /
[ARM64 metadata](../evidence/task0003-arm64-metadata.json) preserve actual output.
The provenance environment reports `linux/arm64`, while its material target and
output descriptor identify AMD64 correctly. Metadata is not a signed release
attestation or a formal SBOM.

## Immutable identities and inspected differences

The base index was read using `docker buildx imagetools inspect
alpine:3.24@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6`.
The common OCI index digest is distinct from these platform manifests:

| Identity / observation | AMD64 | ARM64 comparison |
|---|---|---|
| Base platform manifest SHA256 | `d56c381f961d307a21b3ca004cf1e3910f106644aefb1f43e654c8a56c4fd395` | `260479a1cfaf304c4c20da7f8405d3ce313513dcd534bb743257bdd2fe0f3e2d` |
| Result manifest / Docker `.Id` SHA256 | `dbc288be32f2833223262801f287d4ba1be4594059a9a06001d31b963e2d428a` | `dea86108c2812d9891674e0291af3b59872925e6c462e189a08acf0b3f61f096` |
| Exported config SHA256 (build log) | `7affa7841874770a1072a0e13ba497195434c8c2789b311471a53c8c3ab7a1be` | `0bcae28f7ee60b01039bce6e402c89f3e2215859ac1e340ee5a16d8b57b57112` |
| Inspect `.Architecture` / `.Os` | amd64 / linux | arm64 / linux |
| Inspect `.Size` bytes | 13,068,888 | 13,619,873 |
| APK-reported footprint | 39.1 MiB, 35 packages | 42.6 MiB, 35 packages |
| `/etc/alpine-release` | 3.24.2 | 3.24.2 |
| APK package architecture | x86_64 | aarch64 |
| FRR and tini versions | 10.6.1-r0 / 0.19.0-r3 | same |

All digest entries above are SHA256. Store `.Size` is not uncompressed size or
a security score. Inspect RepoDigests were local `frr-task0003@sha256:<result>`
identities, not proof of registry availability. The prior native ARM64 artifact
and G-2 runtime evidence are unchanged; this new comparison build is not a
replacement runtime qualification.

## Package provenance and offline inspection

The unchanged Dockerfile executes `apk add --no-cache frr=10.6.1-r0
tini=0.19.0-r3`, with APK's normal signature verification, no `--allow-untrusted`,
and repositories `https://dl-cdn.alpinelinux.org/alpine/v3.24/main` and
`https://dl-cdn.alpinelinux.org/alpine/v3.24/community`. Successful signed-package
resolution is observed under that default trust policy, not a separately
performed package-signature audit. Full installed names/versions/architectures
are recorded for [AMD64](../evidence/task0003-amd64-inventory.txt) and
[ARM64](../evidence/task0003-arm64-inventory.txt). All 35 package versions match
between platforms; package architecture and ELF build identities differ.

No-cache does not freeze repositories. Package indexes and dependencies remain
mutable; retaining the base digest, explicit FRR/tini revisions and inventory
does not guarantee bit-for-bit rebuilds or future package availability.
Formal SBOM/CVE/license/security-update acceptance remains NOT RUN.

Static inspection used one uniquely named **never-started** container per image:

```sh
docker create --platform linux/amd64 --name "$name" --network none --cap-drop ALL --security-opt no-new-privileges --memory 256m --pids-limit 128 --entrypoint /bin/true frr-task0003:amd64
docker cp "$name:/lib/apk/db/installed" amd64-inventory/
docker cp "$name:/usr/lib/frr/zebra" amd64-inventory/
file amd64-inventory/zebra
docker rm "$name"
```

The same copy/inspection covered ospfd/bgpd/mgmtd/tini, repositories,
alpine-release and passwd/group for each platform (ARM64 used matching
platform/tag/directory). `file` identified all five AMD64 binaries as x86-64
ELF with `/lib/ld-musl-x86_64.so.1`; ARM64 binaries as AArch64 ELF with
`/lib/ld-musl-aarch64.so.1`. FRR account exists as UID 100/GID 101, frrvty
GID 102 in both. These account files do not prove runtime privilege dropping.
Names were collision-checked; a trap covered forced removal on errors. Both
normal removals returned 0 and exact-name inspect failed afterward: offline
inspection cleanup PASS. No container was started or runtime safety tested.

**AMD64 build warning retained:** several APK install hooks and the BusyBox
trigger reported `Could not resolve /proc/self/fd/7`; the ARM64 build did not.
APK and build returned 0 and FRR accounts/files exist, but this is not evidence
that every hook's runtime effects are correct. The warning's cause and runtime
impact are unverified. Do not patch FRR or change architecture to hide it; check
its impact in the separately authorized native runtime gate before acceptance.

## Static tests and remaining gates

Executed on Workbox (Helm v3.19.0+g3d8990f, Python 3.14.4):

```sh
helm lint charts/frr-route-reflector -f examples/documentation-values.json
helm template rr charts/frr-route-reflector -f examples/documentation-values.json
python3 tests/test_chart.py
```

All exited 0; [captured output](../evidence/task0003-static-tests.txt) records
33 negative cases plus lint/schema/determinism/cardinality/mapping PASS. These
checks are architecture-independent and use documentation values only.

The read-only check for `/proc/sys/fs/binfmt_misc/qemu-x86_64` reported
`qemu-x86_64 host handler not readable/present`. This alone is not a proof that
all emulation mechanisms are absent, but no working authorized isolated Docker
emulation runtime was established. Optional **EMULATED** smoke test: NOT RUN.
No binfmt registration, privileged launch or runtime policy change was attempted.
Native AMD64 tests of both FRR syntax configs, four-daemon integration,
capabilities/seccomp, loopback/VLAN, restart/stop, missing-interface refusal and
forwarding drift: **NOT RUN / BLOCKED** pending a suitable authorized environment.

No Kubernetes, CNI/NAD, admission, Worker, external network, host sysctl or
registry changes occurred. Local task artifacts/images remain on Workbox for
review; the two offline inspection containers were removed. G-3 Issue #9 stays
OPEN/BLOCKED. Draft PR #11 remains an artifact-build proposal awaiting review;
there is no main merge or complete AMD64 runtime acceptance claim.
