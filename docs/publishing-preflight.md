# Task 0004 — public image preparation and publication STOP

Codexによる報告:

Date: 2026-10-15 JST. Accepted source base:
`885e5c97e308b2b1442c378927613b2383dc6408`.
Authority: [Issue #12 assignment](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6191574930)
and [Owner rights confirmation](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6191673478).
Continuation authority: [confirmed destination and finite checks](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6192262441).
Current continuation: [Owner cancelled scanner / local source preparation](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6195095706).
See [actual local staging archive](source-bundle-plan.md) and the
[compact per-origin review / finite remaining gates](third-party-distribution-review.md).
Owner approved `Copyright (c) 2026 si32288564`, MIT for original work, and
represented no employer/third-party rights conflict. This is not an independent
legal audit. Third-party code/text retains its own terms; no blanket MIT grant
is applied to the image, FRR, Alpine or imported material.

## Result matrix and bounded STOP

| Gate | Result / limitation |
|---|---|
| Original-work rights / MIT LICENSE | PASS, explicit Owner confirmation; standard complete text added |
| README status | PASS, PR #6 merged / Issue #5 closed verified; stale text corrected |
| Actual AMD64 + ARM64 APK inventory | PASS, 35 each; versions/expressions/origins/commits compared |
| Machine-readable APK SBOM | Produced; JSON/component consistency and formal CycloneDX 1.6 schema PASS; non-APK completeness NOT VERIFIED |
| Fixed source-recipe traceability | PASS, 25 origin recipes HTTP 200; pkgver/pkgrel match installed versions |
| Source material verification | PASS, 173 recipe-listed input SHA512 and 180 fixed recipe-file identities; not full legal/source-delivery clearance |
| Local source/notice staging archive | PASS creation/checksum/555-member integrity validation; explicitly partial, source/legal completeness BLOCKED |
| All corresponding source, notice texts and recipient access | BLOCKED, incomplete/not delivered; do not publish |
| CVE / independent license scanner | CVE scan NOT RUN — Owner explicitly omitted; vulnerabilities unknown. Independent license scan NOT RUN |
| Recorded disclosure candidates | PASS scoped classification: all 22 matches across both arches are unchanged official APK binary static content; not whole-image security clearance |
| Native AMD64 FRR and G-3 runtime/security acceptance | NOT RUN / BLOCKED, unchanged |
| Docker Hub index / Push / signing / main merge | NOT RUN, explicitly forbidden in this task |

Stop **publication** and hand off this partial preparation for review. A complete
license-compliance or security PASS is not claimed. No FRR/Chart/runtime logic,
architecture, image build, package version or lab environment was changed.
Historical Workbox evidence at closed/unmerged PR #11 commit `6c2384e` is cited,
not cherry-picked or promoted into accepted main. Its deleted remote branch
was not restored. The existing local `.env` remains ignored; its prior local
`.gitignore` edit is preserved but not included in this task commit.

## Executed evidence / reproducibility

Continuation commands, using existing Workbox Python/readelf/jsonschema only:

```sh
timeout 180 python3 tests/classify_packaged_findings.py
timeout 300 python3 tests/prepare_source_manifest.py
timeout 180 python3 tests/collect_notice_texts.py
timeout 90 python3 tests/inspect_packaged_linkage.py
timeout 90 python3 tests/validate_cyclonedx_schema.py
python3 tests/test_prepublish.py
```

These are bounded data/ELF/schema operations, not container startup or scanner
execution. All final commands exited 0. The first schema request returned HTTP
403; the corrected finite official-mirror attempt passed. Data-only file
transfers produced benign tar provenance-xattr warnings; no host settings were
altered. [Continuation consistency output](evidence/task0004-continuation-validation.txt)
is separate from the historical first-stage validation. Twenty-four selected
original legal texts are retained with original-member and stored-file hashes;
complete file-level attribution/linked-work compliance is still not asserted.

Existing candidates were identified with:

```sh
docker image inspect frr-task0003:amd64 frr-task0003:arm64 --format 'arch={{.Architecture}} id={{.Id}} size={{.Size}}'
timeout 180 python3 tests/prepublish_inventory.py frr-task0003:amd64 frr-task0003:arm64
```

The inventory script was supplied over SSH to existing Workbox Python 3.14.4
stdin instead of installing it. It invokes only `docker image inspect`,
`docker history --no-trunc --format '{{json .}}'` and `docker image save`.
Local offline evidence-consistency checks ran with `python3 tests/test_prepublish.py`
and `git diff --check`; both exited 0. [Captured output](evidence/task0004-validation.txt)
also records limited heuristic checks of new artifacts and accepted-source history
for container/Chart/tests/README (not all repository history or a full secret audit).
No container is created/started, and no Docker login, credentials file read,
registry operation or scanner installation occurs. Docker 29.1.3 and the
already-built local candidates were used. The final script exited 0.

See [actual config/layer metadata and APK inventory](evidence/task0004-image-inventory.json),
[APK CycloneDX document](evidence/task0004-apk-sbom.cdx.json), and
[human-readable attribution/obligation matrix](../THIRD_PARTY_NOTICES.md).
Config hashes match the recorded Workbox exports:

| Platform | Local manifest / Docker ID (sha256) | Config (sha256) |
|---|---|---|
| amd64 | `dbc288be32f2833223262801f287d4ba1be4594059a9a06001d31b963e2d428a` | `7affa7841874770a1072a0e13ba497195434c8c2789b311471a53c8c3ab7a1be` |
| arm64 | `dea86108c2812d9891674e0291af3b59872925e6c462e189a08acf0b3f61f096` | `0bcae28f7ee60b01039bce6e402c89f3e2215859ac1e340ee5a16d8b57b57112` |

Recipe availability checks used Python stdlib urllib on Workbox, at most four
concurrent readers and 15-second request timeouts, for fixed main/community
APKBUILD URLs. Every successful body was SHA256-hashed, pkgver/pkgrel inspected
without executing shell code, and its SHA512 source entries recorded in
[recipe probes](evidence/task0004-source-recipe-probes.json). A `last_error: 404`
on a successful community result records the preceding main-path attempt,
not failure of the final recipe URL. Source inputs are reproducible via the
recorded URLs, e.g. `curl --fail --location --max-time 30 '<url>' | sha512sum`;
use pipefail and compare with the fixed recipe. HTTP 200 alone is insufficient.

[Selected source checks](evidence/task0004-source-sample-checks.json) record exact
URLs, sizes and expected/observed SHA512. All four selected downloads matched.
That historical sample is preserved. The continuation additionally checked
173 input files and 180 recipe-directory files, including FRR pre-install,
without changing the frozen image builds. See [the versioned bundle manifest](evidence/task0004-source-bundle-manifest.json)
and [itemized licence/source delivery plan](source-bundle-plan.md). This closes
recipe-listed source availability, not file-level licensing, external helper
completeness, final archive assembly or recipient delivery.

## Recipient source delivery proposal — NOT published

Current local preparation produced a real **partial staging archive**, not a
complete recipient bundle or source offer. The [measured artifact and current
finite gaps](source-bundle-plan.md) supersede earlier not-assembled statements.
The following describes proposed recipient delivery, which remains NOT RUN.

Prefer actual source delivery over issuing an unverified written offer. Proposed
delivery is a versioned, distributor-controlled source asset accompanying each
exact binary release, with a manifest mapping both platform digests to:

1. All 25 exact origin recipe directories at the APK-recorded commits, including
   patches, install scripts, config, source checksums and relevant build scripts.
2. Complete matching upstream source, generated-source inputs and any required
   linked-library sources/relinking materials; build instructions/toolchain
   information and project source at the licensed accepted commit.
3. Original file-level copyright/license/NOTICE texts, applicable exceptions
   and modifications, with documented AND/OR choices and linkage review.
4. A SHA256 manifest, per-input SHA512 verification against the recipes and
   independent download/access verification as a recipient without credentials.

**Proposed host for Owner review:** release-associated GitHub assets in this
public repository, with prominent free source-download directions beside the
Docker Hub binary tag and in the image notices. No asset, release or image was
published here. Exact asset URLs, completeness, access and retention are
NOT VERIFIED. Same-place/equivalent-access suitability across Hub and a separate
source host must be reviewed against GPLv2 section 3 and GPLv3 section 6(d);
do not assume an ordinary upstream hyperlink discharges those obligations.
If that arrangement cannot satisfy the selected terms, require a reviewed
co-located delivery mechanism instead. No generic written offer is issued.

Owner must designate the source custodian, hosting/backup capacity and recipient
support process. Retain matching bundles and notices for the entire binary
availability period and any longer applicable obligations; do not delete source
while binaries remain offered. A written-offer alternative would need separate
qualified review of its text, recipients, fulfilment cost and durations (not a
generic promise; GPLv2 3(b) includes at least three years, and GPLv3 options have
their own conditions). Preserve rollback versions as well as the newest tag.

**Remaining blocker:** the complete recipient bundle and notice selection are
not finished. The [itemized STOP list](source-bundle-plan.md) identifies common
build-helper completeness, generated-data notices, actual linked/alternative
license questions and delivery custody. Selected source/recipe inputs now have
verified hashes and selected original legal texts are committed. This is not
permission to push; seek qualified review of those specific unresolved questions.

## Security and disclosure limitations

**Current:** [Owner continuation 6195095706](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6195095706)
cancels Grype. **CVE scan NOT RUN — Owner explicitly omitted.** No memory/cache
approval, replacement scanner, refresh or resource tuning is requested. Scanner-
only scripts/Dockerfile are removed from this proposed deliverable; their exact
versions remain in immutable commit `36018ba3bbec72c10b3b1ffdba1531bb2c155726`.
Unknown vulnerabilities and limited testing remain risks, not a security PASS.
The following acquisition/staging/capacity records are **historical only**;
their scanner permission requests and next-step proposals are withdrawn.

**Recovery after closed/unmerged PR #13:** [Owner authorization 6194375246](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6194375246)
permits a new proposal PR from accepted main and corrected copy-only staging.
The [new preflight](task0004-grype-recovery.md) reverified the existing inputs,
but STOPPED before build/start: the 2,463,731,712-byte DB alone exceeds the
2 GiB memory limit for tmpfs import/cache. Both CVE scans remain NOT RUN. The
following staging STOP is historical and retained; its staging permission has
been superseded, not the publication/legal STOP.

**Latest scanner continuation:** Owner approved Grype v0.120.1 acquisition and
isolated execution in [Issue #12 comment 6193027470](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6193027470).
Tool archive/checksum/signature verification and compatible current DB checksum
checks PASS. Docker refused pre-start `docker cp` into a read-only rootfs; the
single task container was never started and is confirmed removed. Both
architecture CVE scans remain NOT RUN; no zero-CVE or security PASS claim.
See [commands, identities, failure/cleanup and finite next decision](task0004-grype-stop.md).
The tooling statements in the following paragraph describe the earlier proposal
stage and are preserved as history, not current acquisition status.

`command -v` found no syft, trivy or grype on Workbox or the local development
machine; docker-scout was not on Workbox PATH and `docker scout version` returned
unknown command. Scanner versions/database freshness, CVE counts, severities,
affected-package remediation and independent license-scan results are **NOT RUN**,
not zero findings. The continuation rechecked existing Workbox tooling and
prepared [one pinned Grype v0.120.1 acquisition/DB/isolated-execution proposal](scanner-approval-proposal.md)
for Owner approval or a trusted same-digest report. No scanner binary/container
or DB archive was acquired/executed. Existing jsonschema 4.19.2 did validate the
CycloneDX structure: [formal result](evidence/task0004-cyclonedx-schema.json).
The canonical schema endpoint returned 403; one finite retry used official
specification tag 1.6 schema data and recorded its hash. This is not a CVE scan.

The custom offline heuristic scans config, history and all regular layer entries,
including entries later overwritten, for selected token/private-key/internal-domain
patterns and credential-file names. It is not a general secret scanner and does
not decode every format, inspect all encoded content or prove absence of private
data. Counts are recorded without matching values. No private-key, GitHub-token,
Docker-PAT or credential-file-path matches were observed. The nine generic
internal-looking-domain matches and two credential-assignment matches per
architecture were subsequently classified by an offline comparison against
official Alpine HTTPS downloads of the exact apk-tools/frr version/architecture.
All ten affected ELF files matched those APK payloads byte-for-byte. The 22
recorded matches are thus upstream static content, false positives for
project-added private credentials/lab data; no candidate bytes are published.
See [binary comparison hashes/classification](evidence/task0004-official-binary-comparison.json).
No independent APK signature verification is claimed by that HTTPS comparison,
and it does not clear unknown patterns or establish comprehensive image safety.
It does not include company-specific domain names in the published code.
Two credential-assignment regex candidates per architecture were located in the
ELF `/sbin/apk`. They were **not** found verbatim in the checksum-verified APK
upstream source using the historical sample comparison; that source-text nonmatch
was inconclusive. The exact binary comparison above supersedes its unclassified
status for these recorded matches only. Do not expose their bytes in public logs.
An initial comparison helper over-escaped the regex and yielded zero candidates;
it was corrected and rerun. Only the final two-candidate result is used.

Notice-path heuristic found no license/COPYING/copyright/NOTICE names in the
layers. This is neither a complete legal-text search nor a claim that installing
a `*-doc` package alone would ensure compliance. Required texts and source access
must be explicitly packaged/provided and verified before a publishable rebuild;
the unchanged existing candidates are not declared publishable as-is.

AMD64 APK hook warning `Could not resolve /proc/self/fd/7` remains unresolved;
native AMD64 startup, UID/capability, restart/stop and forwarding guard tests
remain NOT RUN. Explicit lab-sysadmin opt-in grants broad kernel capabilities;
neither image size nor build success proves operational safety. Alpine's
[release policy](https://www.alpinelinux.org/releases/) distinguishes main support
from community support until the next stable release. FRR is a community package;
do not infer its security maintenance lifetime from the base branch end date.
Owner must accept a maintenance/rebuild owner and review current package support
and vulnerability findings before any publication.

## Docker Hub proposal — no registry mutation

**Owner-CONFIRMED public repository:** `docker.io/si60545107/frr-route-reflector`.
Its [management page](https://hub.docker.com/repository/docker/si60545107/frr-route-reflector/general)
is not the OCI image reference. Creation/existence is Owner-confirmed in Issue #12;
this task does not log in, use tokens or verify registry credentials.
**Proposed, unapproved tag:** `v0.1.0-lab.1`. No upload/combined index/signing
authorization or immutable published registry index digest exists. No `latest`,
stable or production designation. The [Docker Personal page](https://www.docker.com/products/personal/)
advertises unlimited public repositories, while [Hub usage docs](https://docs.docker.com/docker-hub/usage/pulls/)
apply pull-rate limits. No paid service is assumed. Exact account entitlement,
current effective limits and authenticated repository access are NOT VERIFIED here;
the repository identity itself is confirmed and needs no repeated Owner name check.

After this PR is reviewed/merged and all gates are resolved, a separately approved
step would package the MIT/third-party notices and accepted matching sources,
then use the existing builder for a local OCI output such as:

```sh
# FUTURE PROPOSAL ONLY — NOT RUN; no registry output
docker buildx build --builder mybuild --platform linux/amd64,linux/arm64 --output type=oci,dest=rr-lab.oci.tar container
```

The [OCI exporter](https://docs.docker.com/reference/cli/docker/buildx/build/)
supports a local image-layout tarball rather than assuming multi-platform
`--load` support. That future candidate's digests will differ if notices/layers change; rerun the
appropriate inventory/security/platform checks against the final bytes. Inspect
the OCI index: both runnable platform descriptors must resolve to verified
manifests/configs; unknown-platform attestation descriptors are not extra runnable
architectures. Existing single-platform digests are NOT a published index digest.
Only after source/compliance/security review and exact public push approval may
the two verified manifests and combined index be uploaded. The tool/command for
uploading the reviewed local OCI layout is to be selected at that execution gate;
do not silently rebuild different bytes in a `--push` command.

After an authorized publication, query the exact versioned tag with
`docker buildx imagetools inspect docker.io/si60545107/frr-route-reflector:v0.1.0-lab.1`,
verify both platform mappings and record the **registry index** SHA256 using
the [registry inspection command](https://docs.docker.com/reference/cli/docker/buildx/imagetools/inspect/). Pin that
index digest in Helm values (repository plus digest), never a local config ID.
No final registry digest is invented here. Public description must retain
experimental/lab-only, native AMD64/G-3 NOT RUN and security limitations.

## Handoff / required decisions

Review MIT and the partial inventory/notice/source plan in this new Draft PR.
Before publication, Owner must resolve source custody/delivery and qualified
license review, explicitly review the unscreened-release risk, retain
the scoped binary classification without treating it as full security clearance,
and separately approve final tag/publication
after accepted documents reach main. This task neither signs nor pushes images,
logs in to registries, changes Kubernetes/host/network settings nor merges main.
