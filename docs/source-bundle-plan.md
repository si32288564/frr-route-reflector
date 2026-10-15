# Local source/notice staging package — publication still STOP

Codexによる報告:

Current authority: [Owner continuation 6195095706](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6195095706).
This supersedes the earlier proposal at immutable commit `36018ba3bbec72c10b3b1ffdba1531bb2c155726`;
all prior source/notice/scanner evidence remains traceable. Grype is cancelled:
**CVE scan NOT RUN — Owner explicitly omitted**. No scanner/resource approval is
requested.

## One actual local artifact

Built/tested on Workbox, 2026-10-16 JST (2026-10-15 UTC), LOCAL ONLY:

- Filename: `frr-route-reflector-v0.1.0-lab.1-sources.1-staging.tar.gz`.
- Actual compressed size: **112,542,493 bytes**.
- SHA256: `b0b3e96b6d023485559eb5d348593a2d1356595bf2a41257357bc0012273f1d5`.
- MANIFEST SHA256: `6ce159c134cf2fb09f489c3aaae4f803e1feb7c516580c371d7781fc164ee025`.
- 554 file/link records plus MANIFEST: **555 non-directory archive members**
  reopened and streamed, with every size/hash/link/path and duplicate check PASS.
- Measured uncompressed file payload including MANIFEST: **116,825,985 bytes**;
  this is not tar-header size or a complete-source legal conclusion.
- File-level `MANIFEST.json`, local archive `.sha256` sidecar,
  `RECONSTRUCT.md`, exact image/config mapping, per-origin matrix and file
  ownership/hash metadata are included.
- Project source commit: `2920cfaed358f7166900eade1771acb1321be9e9`,
  **PROVISIONAL / unmerged**. Container/Chart paths match accepted main.
  Rebind to the eventually accepted revision and final bits before distribution.

This is explicitly a **partial staging archive**. It contains all previously
recorded 173 source inputs / 180 recipe files (112,063,647 bytes), 52 original
unnormalized legal members, 29 additional selected notice/source materials,
the provisional public project tree and metadata/instructions. It is not
asserted to include every legally required helper/attribution or to clear the
libapk/OpenSSL issue. See [finite origin/legal review](third-party-distribution-review.md).

[Measured machine result](evidence/task0004-local-bundle.json),
[25-origin material/path/hash matrix](evidence/task0004-origin-distribution-matrix.json),
and [selected legal facts/notices](evidence/task0004-license-facts.json).
No binary archive is in Git or uploaded. The local task directory is identified
to Owner in the chat; public evidence uses relative staging paths, not private
host/user identifiers.

## Execution and historical failure, not invented success

The original preparation probes verified downloaded bodies in memory but did
not persist the source payloads. Read-only inspection of the two existing Task
0004 workspaces confirmed that only records/scripts/scanner inputs remained.
For this actual packaging operation, only missing/incomplete files were
materialized from the **already frozen exact URLs/hashes**, not a renewed origin
or version study. Matching local cache entries were reused (124 on the completed
pass); source SHA512/SHA256 and recipe Git blob SHA1/SHA256 were checked.

The first pass failed with `Disk quota exceeded` despite initial `df` free
space passing the estimate. This is retained as FAIL, not hidden. The canceled
scanner's four task-owned temporary payloads (raw DB, compressed DB, Grype
archive and binary) were each rehashed against the recorded identities, then
deleted; original scan evidence/checksum/signature metadata and FRR exports were
kept. About 2.7 GB was recovered without tuning RAM/disk limits or changing host
settings. These downloaded payloads can be reacquired from the recorded official
sources if later separately authorized. No other user's files were removed.

The same packaging workspace was reused; intact matching source files were not
downloaded again. The completed materialization pass began with 3,540,254,720
free bytes, an estimated 324,790,590-byte packaging allowance and a
201,326,592-byte reserve. Only fixed-source data was downloaded; no source,
APKBUILD, FRR program or scanner was executed. Two targeted fixed-commit root
COPYING paths returned 404; those attribution gaps remain explicit. The
original upstream MPL text was additionally retrieved from Mozilla.

Executed on Workbox with existing Python/tar/zstd only:

```sh
timeout 420 python3 stage_source_bundle.py <task-workspace>
python3 inventory_source_files.py <frozen-inventory> <existing-exports> <output-json>
timeout 90 python3 review_source_notices.py <task-workspace>
timeout 180 python3 assemble_source_bundle.py <task-workspace>
sha256sum -c frr-route-reflector-v0.1.0-lab.1-sources.1-staging.tar.gz.sha256
```

The first materialization failed as above; corrected finite continuation and
final assembly/stream verification passed. Legal-source completeness is
**BLOCKED**, not PASS. A full distro rebuild, recipient download, external
helper fulfilment and legal acceptance were not executed.

## Finite publication mode / remaining decision

[Reconstruction/recipient instructions](source-bundle-reconstruction.md) give
the actual layout, exact future naming, checksum verification, provenance,
package-specific source workflow and stewardship proposal.

Prefer a reviewed versioned GitHub Release asset, after completing the narrow
gaps, named `frr-route-reflector-v0.1.0-lab.1-sources.1.tar.gz` with checksum.
Binary reference remains the Owner-confirmed
`docker.io/si60545107/frr-route-reflector`; `v0.1.0-lab.1` is proposed only.
No source asset URL is invented and no written offer is issued. GPLv2 section 3
and GPLv3 section 6(d) require their respective suitable delivery arrangements;
Hub-to-GitHub equivalent access is not automatically approved. One finite
alternative is a reviewed co-located binary/source download endpoint, not an
unconditional new source layer in every image.

Owner must explicitly accept stewardship/retention/recipient support; final
source/notice completeness, legal basis, public access, final accepted revision
and release risk remain separate gates. Keep Issue #12 Open / PR #14 Draft.
No Docker Hub Push, GitHub Release, signing, main merge or Kubernetes changes.
