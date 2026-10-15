# Local staging bundle — reconstruction and verification

This is a **partial prepublication staging package**, not a source offer,
published asset, legal clearance or permission to redistribute the images.
Original project code is MIT; third-party members retain their original terms.
CVE scan NOT RUN — Owner explicitly omitted; vulnerabilities are unknown.

## Recipient procedure (local test now; public access NOT RUN)

1. Obtain the exact archive and its SHA256 sidecar from the distributor's
   reviewed versioned release. No such public release exists yet. Verify the
   archive SHA256 against the separately reviewed record, not just an untrusted
   checksum downloaded alongside an untrusted archive.
2. List the archive before extraction. It must contain only relative paths
   below its versioned root, without traversal, absolute links or duplicate
   members. Extract into a new empty unprivileged directory, never over host
   settings, a repository or an existing source tree.
3. Read `MANIFEST.json`: compare each regular file SHA256/size and any symlink
   target to the manifest. The manifest does not list its own digest; the
   external archive SHA256 binds it. Inspect `metadata/` for both exact local
   image/config IDs, ownership/file hashes and source-input provenance.
4. Check original input SHA512 against the frozen source manifest in
   `project/docs/evidence/task0004-source-bundle-manifest.json`; recipe files
   also have their original Git blob SHA1 and SHA256. Input archives stay intact
   under `origins/<origin>/<version>/inputs/`. Do not apply patches twice.
5. Locate the pinned APKBUILD under the corresponding `recipe/main/...` or
   `recipe/community/...` directory. It controls source aliases, patch order,
   configure/build/package/install hooks and subpackage selection. All its
   recorded origin-directory files and source inputs are included. Upstream
   configure/Makefile/Meson and install controls stay inside the original input
   archives. Do not source/run those scripts merely to verify a checksum.
6. For a separately authorized rebuild, use an appropriate isolated Alpine
   3.24 build environment for x86_64 or aarch64 and the original APKBUILD/abuild
   workflow with its dependencies and local input cache. No rebuild is performed
   by this package. The exact original external abuild/toolchain revision was
   not captured; confirm any required helper version/material before asserting
   complete corresponding-source fulfilment. Ordinary unmodified compilers,
   packaging tools and system libraries are not automatically all part of every
   program's corresponding source; their treatment needs the applicable terms.
7. Project `container/` and `charts/` are a provisional source-commit binding,
   identified in MANIFEST. They match accepted-main implementation paths; the
   MIT/notices preparation commit itself is still unmerged. Rebind/repackage
   to the eventually accepted release revision and final binary digests before
   any distribution. Version-pinned mutable APK repositories do not promise
   bit-identical rebuilds or permanent availability.

## Notice/source scope

`notices/original/` contains exact, unnormalized upstream legal members;
`notices/additional/` contains selected missing legal texts/headers, FRR's
`doc/licenses`, Mozilla certdata/MPL material and musl-utils source headers.
`project/licenses/third-party/` preserves the historical 24 normalized notice
texts with their separate raw/stored hashes. These are not relicensed as MIT.

Full source for permissive origins is included for traceability/notice recovery,
not because all installed permissive packages require a source offer. Original
expressions remain unchanged. Proposed alternative paths (BSD for libcap/psx
and zstd; GPL-2.0-or-later for libelf library; GPLv3-compatible vtysh/Readline)
are supported by selected original grants, not a general legal certification.

Outstanding category gaps are explicit: generated Alpine data MIT attribution
and the small ldconfig wrapper's attribution; original external abuild/helper
binding as applicable; libapk/OpenSSL distribution basis; final notice placement
and recipient access/retention. Do not label this archive complete until those
specific items have been reviewed. No written offer is issued.

## Proposed publication mode — NOT PUBLISHED

Intended future asset names after review:
`frr-route-reflector-v0.1.0-lab.1-sources.1.tar.gz` and matching `.sha256`.
The actual local artifact has `-staging` in its name and is not a release asset.
Proposed binary reference: `docker.io/si60545107/frr-route-reflector:v0.1.0-lab.1`.
The repository is Owner-confirmed; the tag and binary release are NOT AUTHORIZED.

Prefer a versioned GitHub Release source/notice asset, with prominent download
directions alongside the exact Docker Hub tag and in its accompanying notices.
Do not invent an asset URL or claim that an upstream project hyperlink fulfils
our obligations. GPLv2 section 3 and GPLv3 section 6(d) have distinct source
conveyance options; cross-host Hub-to-GitHub equivalent access requires review.
One finite alternative is a reviewed co-located binary/source download delivery
endpoint, rather than an unconditional source layer in every OCI image.
Neither mode is implemented or legally cleared here.

Owner is the proposed accountable steward and must expressly accept custody,
backup/recipient support and retention before release. Keep matching archives,
checksums and notices for every offered binary version throughout availability
and any longer applicable duties. This is not a generic three-year written
offer. Do not delete old sources while matching binaries remain available.

Before an eventual approved release, test the exact source download as an
unauthenticated recipient on a separate machine, verify checksum/manifest and
the binary mapping, and check that directions are visible beside the binary.
Public download, retention commitment, final notice packaging and final accepted
source/image binding are **NOT RUN / BLOCKED**, distinct from local archive
creation/integrity verification. No registry index digest is inferred from local
per-platform image/config IDs.
