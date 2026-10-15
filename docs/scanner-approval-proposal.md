# One scoped scanner proposal — NOT acquired or executed

**ARCHIVED / CANCELLED:** Owner omitted CVE scanning in Issue #12 comments
6194976836 and 6195095706. All approval requests below are historical, not
current obligations. No rerun, replacement scanner or resource change is planned.

**Historical proposal at commit 5414be3.** Owner subsequently approved the
bounded acquisition/verification in Issue #12 comment 6193027470. The
[2026-10-15 execution continuation](task0004-grype-stop.md) records verified
tool/DB acquisition and a pre-start Docker staging STOP; both CVE scans remain
NOT RUN. The original proposal below is retained as approval history, not a
statement of current acquisition status.

Issue #12 comment 6192262441 authorizes proposing, not installing/downloading or
running a new scanner. Existing Workbox syft/trivy/grype probes still returned
NOT ON PATH. Formal CycloneDX validation used already installed jsonschema
4.19.2; it is not a CVE or license audit.

## Single proposed tool and provenance

**Grype v0.120.1**, Linux ARM64, running on the already authorized ARM64 Workbox.
Official [immutable release metadata](https://api.github.com/repos/anchore/grype/releases/tags/v0.120.1)
was read without credentials. No executable archive was downloaded.

- Artifact: `https://github.com/anchore/grype/releases/download/v0.120.1/grype_0.120.1_linux_arm64.tar.gz`
- Release API artifact digest: `sha256:29f47391dc283aa79fcc38e65224cd61f64dec0ecfd0db7074128ebf8ff23514`.
- Checksums: `grype_0.120.1_checksums.txt`, API digest
  `sha256:c25b6095265b44fd9bbb9dbe76aca8daa394c5f0490793d2b52b16be4f5b71b1`.
- Signature bundle: `grype_0.120.1_checksums.txt.sigstore.json`, API digest
  `sha256:d6e9cd7e0e1c0384eb7f880640c61498388370d4bbf068ed3f84fc1941c511e8`.

After approval, verify the archive hash against this pinned identity, the
release checksum and the signature/expected Anchore release workflow identity
using already available verification tooling. Do not equate API metadata with
independently completed signature verification; that verification is NOT RUN.
Reject a mismatch and stop rather than choosing another version silently.

DB provenance: Anchore's [Grype DB publisher](https://oss.anchore.com/docs/architecture/grype-db/),
with the schema appropriate to this release obtained from
`https://grype.anchore.io/databases/v6/latest.json` (schema compatibility must be
confirmed before execution). Record its built time, resolved archive URL and
checksum, verify the archive, and freeze that snapshot for both platform scans.
No DB archive was downloaded under this task. If its schema is incompatible or
the snapshot is stale/unverifiable, STOP for a corrected approval; do not guess
zero vulnerabilities or disable checksum/freshness checks.

## Proposed isolated execution, requiring one explicit Owner approval

Scope: acquire this one tool and compatible current database as data in a
unique temporary directory on Workbox; run against Docker-save archives of the
two frozen local manifest identities recorded in Task 0004. Never scan by a
mutable registry tag, send archives to a remote scanning service, or log in to
Docker Hub. Export/hash each archive first and recheck source image identity.

Proposed execution uses existing native ARM64 Alpine runtime bytes only as a
sandbox: create an unprivileged, unique disposable container with entrypoint
the verified Grype binary, **not FRR**. Copy scanner, DB and target archives
using `docker cp` before start. Network none, uid/gid 65534, cap-drop ALL,
no-new-privileges, Docker default seccomp, read-only rootfs, bounded writable
tmpfs only for temporary/cache needs, memory 2 GiB, pids 64, external timeout
10 minutes, and trap/explicit exact-container removal and absence check.
No host directory/socket/device mounts, no host namespaces and no privileges.
The container sandbox does not execute target-image programs. If the binary or
DB cannot operate under those controls, STOP rather than relax them silently.

Future proposed scan commands inside the approved sandbox:

```sh
# NOT RUN; first copy the verified /work/db into container-private /tmp/grype-db.
# Inputs are reviewed Docker-save archives, not registry references.
GRYPE_DB_CACHE_DIR=/tmp/grype-db GRYPE_DB_AUTO_UPDATE=false GRYPE_CHECK_FOR_APP_UPDATE=false /work/grype docker-archive:/work/amd64.tar -o json --fail-on high
GRYPE_DB_CACHE_DIR=/tmp/grype-db GRYPE_DB_AUTO_UPDATE=false GRYPE_CHECK_FOR_APP_UPDATE=false /work/grype docker-archive:/work/arm64.tar -o json --fail-on high
```

Keep DB writes/cache in the approved container-private area; no host secret
environment or Docker credentials are copied. Acquisition/verification happens
before the network-none scan. Grype's [archive input support](https://oss.anchore.com/docs/reference/grype/cli/)
does not require mounting the Docker socket. This proposal is not a claim the
sandbox has already been tested.

Output required: tool/config/DB identities and age, input archive/config/manifest
hashes, package CVE/severity/fix availability and match limitations for both
architectures. High/critical findings trigger finite remediation or explicit
Owner risk disposition before publication; tool exit code alone is not release
acceptance. Re-run on final changed image bytes. Formal license interpretation,
corresponding-source fulfilment and comprehensive secrets clearance are not
replaced by this CVE scan.

**Owner decision requested:** approve exactly this scoped acquisition/verification
and isolated execution, or provide a trusted same-digest report. Until then:
scanner acquisition/execution NOT RUN; CVE counts, severity and fixes NOT RUN.
