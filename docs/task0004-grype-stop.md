# Task 0004 — approved Grype acquisition; isolated staging STOP

Codexによる報告:

2026-10-15 UTC. Authority: [Owner approval 6193027470](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6193027470).
This is an append-only continuation of the earlier NOT RUN scanner proposal,
not a replacement for previous license/source/security evidence. Accepted main
remains `885e5c97e308b2b1442c378927613b2383dc6408`.

## Outcome

**STOP: Docker 29.1.3 refused the approved pre-start copy into the read-only
container root filesystem. No scanner or target-image program was executed.**
One unique task container was created, never started, removed with exit 0, and
confirmed absent twice with exact-name inspect. No retry or security relaxation
followed. Both image vulnerability scans remain **NOT RUN**, not zero findings.

| Check | Result |
|---|---|
| Existing AMD64/ARM64 image IDs and exported config hashes | PASS, match approved frozen candidates |
| Grype release archive/checksum/bundle SHA256 | PASS, all three approved pins match |
| Official checksum line for archive | PASS |
| Sigstore checksum signature / exact Anchore workflow + GitHub OIDC | PASS, existing cosign; no insecure flags |
| Compatible DB acquisition / archive SHA256 / age | PASS, v6.1.10 active, 7h 1m 46s old at check, below 120h |
| Create isolated stopped sandbox | PASS, Docker create exit 0; never started |
| Pre-start `docker cp` | FAIL, exit 1: `Error response from daemon: container rootfs is marked read-only` |
| Grype runtime version / DB import and in-scanner checks | NOT RUN |
| AMD64 and ARM64 CVEs / severities / fixes | NOT RUN / BLOCKED at staging |
| Exact task-container removal / absence | PASS, removal 0; absence inspect 1, `No such container` |
| License clearance, native AMD64 FRR, Kubernetes G-3 | Still BLOCKED / NOT RUN; not tested by this work |
| Docker Hub login/push, source assets/signing, main merge, Kubernetes changes | NOT RUN; remain unauthorized |

The entire scripted attempt took **13.137206 seconds**
(`13:32:21.645902`–`13:32:34.783108` UTC). Runtime duration is **not applicable**:
`docker start` was never reached. No vulnerability JSON exists to sanitize or
summarize. The [machine execution record](evidence/task0004-grype-execution.json)
contains image/archive/config hashes, DB/tool identities, attempted commands,
timestamps and cleanup results. Private host paths are replaced with
`<task-temp>`; no credentials or private lab identifiers are recorded.
[Local offline validation](evidence/task0004-grype-validation.txt) passed Python
compilation, evidence consistency and the limited disclosure heuristic; this
does not validate the scanner's unexecuted runtime or prove absence of secrets.

## Provenance and verification chronology

Official Grype v0.120.1 Linux ARM64 release inputs were acquired once into a
unique temporary Workbox directory, not installed on PATH. SHA256:

| Input | SHA256 |
|---|---|
| `grype_0.120.1_linux_arm64.tar.gz` | `29f47391dc283aa79fcc38e65224cd61f64dec0ecfd0db7074128ebf8ff23514` |
| `grype_0.120.1_checksums.txt` | `c25b6095265b44fd9bbb9dbe76aca8daa394c5f0490793d2b52b16be4f5b71b1` |
| `grype_0.120.1_checksums.txt.sigstore.json` | `d6e9cd7e0e1c0384eb7f880640c61498388370d4bbf068ed3f84fc1941c511e8` |
| Extracted `grype` executable, NOT EXECUTED | `94afbea0a9b65a3a83b820e622e8ac337e26608c860315208d58dad9a80b25db` |

1. Initial signature verification **FAIL**: Codex initially assumed a tag-ref
   certificate regex (`.../workflows/[^/]+@refs/tags/v0\.120\.1$`). Actual SAN was
   `https://github.com/anchore/grype/.github/workflows/release.yaml@refs/heads/main`.
   No binary execution or DB download followed that failure while investigating.
2. Independently read the fixed-tag [official release workflow](https://github.com/anchore/grype/blob/v0.120.1/.github/workflows/release.yaml):
   it uses manual dispatch to tag/release main. The tag-only regex was Codex's
   incorrect assumption, not an Owner-prescribed identity. The official
   [verification guidance](https://oss.anchore.com/docs/installation/verification/)
   identifies Anchore's GitHub workflow and OIDC issuer.
3. Reverified the **same pinned checksum and bundle**, with the exact confirmed
   workflow identity (not a wildcard), and
   `--certificate-oidc-issuer https://token.actions.githubusercontent.com`:
   **PASS, exit 0, `Verified OK`**. Repeated inside the recorded script before
   preparing inputs, also PASS. Existing `/usr/bin/cosign` reports GitVersion
   `devel`, GitCommit `unknown`, Go 1.25, linux/arm64; no verifier was installed.
   This cryptographic verification does not itself audit the scanner's code.

Only afterward was the one database archive downloaded. Official v0.120.1
[DB schema constants](https://github.com/anchore/grype/blob/v0.120.1/grype/db/v6/db.go)
are 6.1.10; the publisher's `https://grype.anchore.io/databases/v6/latest.json`
advertised active **v6.1.10**, built **2026-10-15T06:30:36Z**. Frozen archive:

`https://grype.anchore.io/databases/v6/vulnerability-db_v6.1.10_2026-10-15T00:29:08Z_1792045836.tar.zst`

- Archive SHA256: `2f1597f25b5089e966272b251eb4d1f9977e59d57029af1c8810deb6e5321aa2`,
  exactly matching the publisher's metadata. Download HTTP 200, 190,523,958 bytes.
- Response `Last-Modified`: **2026-10-15T07:17:40Z**; response `Date`:
  **2026-10-15T13:29:09Z**. Last-Modified is an HTTP object timestamp, **not an
  independently attested publication time**. Exact publication time is unknown;
  neither filename timestamp nor Last-Modified is substituted for DB built time.
- Archive listed only `vulnerability.db`; extracted data-file SHA256:
  `594802efcf4166565db7992f9aa4dd3f3be59bc7f266cbbf49ea0bec0c261cbb`.
- This is HTTPS publisher/checksum consistency, **not an independently signed
  DB provenance assertion**. One snapshot was frozen for both architectures,
  but neither scan ran. No DB checksum/freshness check was disabled.

## Reproduction and exact boundary

[The diagnostic script](../tests/scan_packaged_frr.py) expects the already
acquired approved inputs in a unique `/tmp/frr-task0004-grype.*` directory.
It does not download/install anything. Actual invocation on existing Workbox:

```sh
python3 scan_packaged_frr.py <task-temp>  # exit 1, STOP at docker cp
```

The command list is retained verbatim except temporary-path normalization in
the JSON record. Both Docker-save exports preceded container creation; their
config SHA256 values match the previously recorded per-platform manifests.
The sandbox used already-present native ARM64 Alpine 3.24 bytes with the pinned
reference, `--pull never`, Grype entrypoint, uid/gid 65534, network none,
drop ALL, no-new-privileges, no seccomp override (Docker default intended),
read-only rootfs, memory and memory+swap 2 GiB, PIDs 64, private `/tmp` tmpfs
512 MiB with noexec/nosuid/nodev. No host mounts/devices/namespaces were requested.
DB automatic update and app update were disabled; age/hash checking explicitly
enabled, maximum age 120h, `--fail-on high` set.

The prepared runtime limit was external GNU timeout TERM at 595 seconds plus
5-second kill grace (600 seconds maximum), with exact-container finally cleanup.
It was **NOT exercised**, because input staging failed before start. Inspect
of actual running capabilities/seccomp/namespace state and timeout behavior
are also **NOT RUN**; create flags alone are not runtime proof.

Immediate observable cause:

```text
docker cp <task-temp>/payload/. <unique-task-container>:/work
Error response from daemon: container rootfs is marked read-only
exit 1
docker rm -f <unique-task-container>  # exit 0
docker container inspect <unique-task-container>
Error response from daemon: No such container: <unique-task-container>
exit 1
```

Do not rerun this script without a reviewed resolution; the frozen DB will
also eventually become stale. No general Docker staging experiments followed.
Temporary downloads/exports remain in the restricted task directory for local
review only; no scanner executable, database or image archive is committed.

## Finite next decision — no implementation performed

The approved sequence combines a read-only rootfs **from creation** with a
pre-start copy into that same filesystem. This Docker rejects it. Changing
rootfs permissions, using a mount, changing entrypoint, or constructing a new
scanner image is not silently inferred from this approval.

One additional preparation issue is known from source inspection, **not observed
in a running scanner**: the publisher archive has no installed `import.json`.
The standard [Grype DB import/hydration path](https://github.com/anchore/grype/blob/v0.120.1/grype/db/v6/installation/curator.go)
creates indexes and import metadata in writable cache. No import metadata was
fabricated and no checksum validation bypassed. Copying the raw DB elsewhere
would not by itself demonstrate a ready-to-scan cache.

For Chat/Owner review, choose one bounded path:

1. **Approve a corrected disposable staging/init plan:** a local temporary
   scanner image assembled from only the same existing Alpine bytes, verified
   scanner and frozen data (no Dockerfile RUN/network/package installation),
   plus explicitly approved existing-base initialization commands to copy the
   DB into bounded private tmpfs, run verified Grype's standard DB import, then
   exec the verified scanner. Final scanner keeps the same uid, capabilities,
   readonly rootfs, network isolation, resource limits and external timeout.
   This changes the approved entrypoint/staging sequence and needs review
   **before** creating/building/running it. Feasibility of DB hydration within
   the existing 2 GiB limit remains untested; no automatic resource increase.
2. **Provide a trusted same-image/config-digest report**, including scanner/DB
   identities, actual findings, controls and timestamps, for review instead.

No new FRR architecture, supervisor, runtime privileges or Kubernetes changes
are proposed. CVE counts, severities, fixes and risk disposition cannot be
invented without results. High/critical findings in a later authorized scan
would require finite remediation or explicit Owner risk acceptance before any
publication. Remaining source/notice/legal fulfilment and release approval are
unchanged. Keep Issue #12 Open and PR #13 Draft.
