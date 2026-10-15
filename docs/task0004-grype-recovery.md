# Task 0004 recovery — new proposal branch; DB capacity STOP

Codexによる報告:

2026-10-15 UTC. Authority: [Owner recovery authorization 6194375246](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6194375246).
**STOP before scanner build/start: the verified database alone exceeds the
approved 2 GiB memory limit for the required tmpfs import/cache.**

## Source recovery, not acceptance or reopening

Live main was fetched immediately before branching and remained
`885e5c97e308b2b1442c378927613b2383dc6408`. New branch:
`codex-task0004-grype-recovery`. The usual `codex/` prefix conflicts with the
existing local `codex` ref; it was not deleted or renamed to create a prefix.

Only the 52 Task 0004 paths in the main-to-
[`a75d4d77633328582b0395f493a42e6d9407b493`](https://github.com/si32288564/frr-route-reflector/commit/a75d4d77633328582b0395f493a42e6d9407b493)
diff were brought forward: LICENSE/README/THIRD_PARTY_NOTICES, Task 0004
preparation docs/evidence, 24 third-party legal texts, and eight Task 0004 test
helpers. No Container/Helm implementation, architecture, environment bindings,
`.env` or unrelated `.gitignore` change was imported. The three scoped commits
were cherry-picked with `-x` after checking their path scope; the recovered
tracked tree matched a75d4d7 before new changes. Original references remain in
commit messages. **These are unmerged proposals**, not newly accepted main.
Closed/unmerged PR #13 was not reopened and its deleted branch was not restored.
Earlier PASS/FAIL/STOP records remain unchanged.

## Actual checks and new STOP

[Executed preflight](evidence/task0004-grype-recovery-preflight.json), using
existing Python, tar/zstd, cosign and read-only Docker image inspect:

```sh
python3 preflight_grype_recovery.py <existing-task-temp>  # exit 1: capacity STOP
```

The script took **7.522029 seconds** (`14:27:51.095355`–`14:27:58.617384` UTC).
It rehashed all pinned tool inputs and the extracted scanner, verified the
checksum signature with exact previously confirmed release workflow identity,
checked the signed checksum line, and revalidated the same DB, base image and
both original FRR image/config/export identities. **Grype was never executed.**

| Check | Result |
|---|---|
| Grype 0.120.1 archive/checksum/bundle hashes + signature | PASS, same approved bytes; cosign exit 0 `Verified OK` |
| DB SHA256/schema/age | PASS, same v6.1.10 snapshot; 7h57m16s old, below 120h |
| Frozen AMD64/ARM64 image/config/archive identities | PASS, match previous evidence |
| Local pinned ARM64 Alpine base identity | PASS, unchanged |
| Necessary tmpfs/memory capacity | FAIL, DB alone exceeds limit by 316,248,064 bytes |
| Temporary scanner image build / layer inspection | NOT RUN, preflight STOP |
| DB import / installed metadata / runtime controls | NOT RUN |
| Both CVE reports, severity/fix lists and risk acceptance | NOT RUN / BLOCKED, not zero findings |
| New scanner containers/images/build contexts | None created; no cleanup targets or residual scanner artifacts from this attempt |
| Local consistency/AST/shell syntax and formal SBOM schema | PASS, scoped validation only |
| Distribution/license clearance; native AMD64/G-3 | Remain BLOCKED / NOT RUN |

Exact capacity evidence:

| Quantity | Bytes |
|---|---:|
| Publisher DB archive, compressed | 190,523,958 |
| Archive member `vulnerability.db` | **2,463,731,712** |
| Previously extracted file logical size | **2,463,731,712** |
| Previously extracted file allocated size | **2,463,731,712** |
| Approved memory maximum | **2,147,483,648** |
| Minimum excess, excluding Grype/index/temp overhead | **316,248,064** |

Archive member size was independently read with
`tar --zstd --numeric-owner -tvf <task-temp>/db.tar.zst`; no new extraction was
performed. The existing extracted DB was rehashed as
`594802efcf4166565db7992f9aa4dd3f3be59bc7f266cbbf49ea0bec0c261cbb`.
The size is not merely a sparse-file allocation assumption: allocated bytes
also equal logical bytes. [Docker documents that tmpfs usage counts against the container memory cgroup](https://docs.docker.com/engine/storage/tmpfs/).
Thus a larger tmpfs mount size alone cannot solve the 2 GiB limit. This is a
necessary-capacity failure, **not an observed OOM or an executed import failure**.
There is no need to exhaust host memory to establish this blocker.
The previously recorded `--memory 2g --memory-swap 2g` combined limit is
preserved in this assessment; extra swap is not assumed as an implicit
workaround for the unchanged resource limits. No swap/host setting was changed.

Same DB archive SHA256:
`2f1597f25b5089e966272b251eb4d1f9977e59d57029af1c8810deb6e5321aa2`.
Built `2026-10-15T06:30:36Z`, publisher/schema unchanged. Exact publication time
remains unknown; prior HTTP Last-Modified is not a signed publication timestamp.
No refresh was needed or attempted. No smaller/older DB, alternative scanner,
schema change, checksum bypass, or stale-age override was substituted.

## Corrected staging/init plan — static only, NOT BUILT/RUN

The approved correction is represented by
[copy-only Dockerfile](../tests/grype-sandbox/Dockerfile) and
[small audited init script](../tests/grype-sandbox/init.sh). No `docker cp` into
read-only rootfs recurs. A future unique temporary context would contain only
the fixed Dockerfile, verified scanner, verified compressed DB, two hash-bound
Docker-save archives and this task-owned init script; no credentials, private
extras, package install, RUN instruction or registry pull. Both archive programs
remain data. Do not execute this plan until the capacity STOP is resolved.

Pinned v0.120.1 source confirms the supported commands:

- [`grype db import FILE`](https://github.com/anchore/grype/blob/v0.120.1/cmd/grype/cli/commands/db_import.go)
  invokes the standard import/hydration flow; no synthetic `import.json`.
- [`grype db status -o json`](https://github.com/anchore/grype/blob/v0.120.1/cmd/grype/cli/commands/db_status.go)
  returns metadata and a nonzero status if DB validation fails.
- Init would run these in a bounded private tmpfs, then exec verified Grype
  against `docker-archive:` with JSON stdout and `--fail-on high`. Diagnostics
  and DB status go to stderr; auto-update stays OFF, hash/age checks stay ON.

Any later approved runner must still impose readonly rootfs, network none,
65534:65534, cap-drop ALL, no-new-privileges, Docker default seccomp, no host
mounts/devices/namespaces, PIDs 64 and externally enforced total at most 600s
per architecture **including initialization**, with exact owned-artifact
cleanup. Valid HIGH/CRITICAL reports must not prevent the other architecture's
scan; unexpected operational failures STOP. None of those runtime claims is
asserted from static plan checks.

## Finite decision requested; no changes performed

Owner/Chat should review **one** corrected resource/storage bound before rerun:

1. Permit an explicitly larger scanner-only memory/tmpfs budget after checking
   host headroom, accounting for the measured 2.46 GB DB **plus** hydration/index
   and process overhead. A particular larger value is not asserted sufficient.
2. Alternatively authorize a bounded, task-private **filesystem-backed cache**
   with explicit capacity/cleanup, while preserving the 2 GiB RAM and all other
   isolation. This is outside the approved tmpfs-only plan; no volume/mount,
   storage provisioning or quota/configuration change was attempted.

Both require new review; no host changes, software install or privilege increase
is inferred. Do not remove DB records/indexes, fake import metadata or filter
vulnerabilities to fit. No further runtime/build exploration followed STOP.
No CVE risk disposition is possible without actual reports. Existing legal,
source/notice delivery/custody, final-image, native AMD64 and G-3 gates remain.
No Docker Hub login/token/push, image signing, release/source publication,
main merge or Kubernetes change. Keep Issue #12 Open and new PR Draft.

## Verification and artifact handling

Python compilation/AST and `sh -n` PASS. Existing consistency/disclosure checks
PASS within their stated limitations, not an exhaustive secret audit.
Formal CycloneDX 1.6 validation reran with existing jsonschema 4.19.2:
[record](evidence/task0004-grype-recovery-schema.json), errors=[], exit 0.
The canonical schema endpoint again returned 403; the existing finite fallback
fetched the same fixed official schema hash. RefResolver emitted a deprecation
warning; no tool was installed or upgraded. Prior source/recipe/notice/binary
comparison retrievals were not repeated.

Scanner binary, publisher DB and image exports stay only in the existing local
task directory; no binary archive enters Git. This attempt created no scanner
container/image/context, so no new runtime cleanup or container-absence test is
claimed. Previous task-container removal remains separately documented in the
unchanged earlier STOP record; exact-name inspect again returned exit 1 / No such
container. Schema-only scratch copies/directories were removed and absence
checked (exit 0); original files and committed results remain available. The
small preflight script/JSON remain task-owned in the existing local directory.
No pre-existing settings, containers or images were modified. See the
[validation log](evidence/task0004-grype-recovery-validation.txt).
