# Frozen candidate source/notice bundle — v0.1.0-lab.1-sources.1 proposal

This is preparation under Issue #12 comment 6192262441, not a source offer,
published release asset, legal opinion or permission to push a container image.
Project-original material is MIT; bundled components retain their own terms.

## Concrete manifest and measured capacity

[Versioned manifest](evidence/task0004-source-bundle-manifest.json) maps the
35 packages on each architecture to 25 aports origins/versions/commits and
the two exact local image manifests. One shared source set covers those APK
origins; architecture-specific binary checksums remain in the original inventory.

- **173 source inputs** retrieved and matched to the pinned recipe SHA512:
  111,658,552 bytes total. Each record has exact filename, verified download URL,
  SHA512, SHA256, size and identified archive legal-file paths/hashes.
- **180 recipe-directory files** retrieved at recorded aports commits and
  checked against Git blob identities: 405,095 bytes total, including build,
  install and patch material. No directory/symlink gaps were reported by this
  bounded directory inventory. Common external build helpers are not covered by
  that statement.
- Payload sum for the specified no-deduplication layout is **112,063,647 bytes**
  (~106.9 MiB), before archive headers, project source and additional legal texts.
  Budget approximately **113–116 MB plus any unresolved helper material** for
  an uncompressed tar layout; final size/hash is NOT RUN until assembled.
  Do not interpret this as a measured complete archive size. No binary source
  archives are committed to Git or published.

Finite reproduction on Workbox with existing Python only:

```sh
timeout 300 python3 tests/prepare_source_manifest.py
timeout 180 python3 tests/collect_notice_texts.py
```

The first command reads the preserved recipe/image evidence, downloads HTTPS
data only (at most four concurrent source readers; fixed size/count/time bounds),
checks hashes and lists legal material; it does not execute APKBUILD or source.
The second selects original legal text members from verified archives. Both
were run, not proposed scanner operations. HTTPS source availability was
verified without registry credentials. Large archives were inspected in memory,
not installed. Source asset publication and recipient access to our own final
bundle remain NOT RUN. Required notices are not inferred from maintainer names.

Proposed layout: `origins/<origin>/<version>/recipe/` for exact recipe files,
`origins/<origin>/<version>/inputs/` for verified upstream/patch inputs,
`project/<accepted-license-commit>/` for project source and MIT grant, and
`notices/` plus manifest/hashes and reconstruction instructions. Preserve origin
and file boundaries; do not accidentally apply a patch twice when reconstructing
the build. Retain recipe SHA512 checks along with our bundle SHA256 inventory.

## Specific distribution paths, not a blanket source demand

The following are planning paths subject to the stated remaining file/linkage
questions. The original package AND/OR expressions remain unchanged in the SBOM.

| Installed component(s) / origin | Applicable preparation path | Current material / narrow gap |
|---|---|---|
| alpine-baselayout(+data), apk-tools/libapk, BusyBox/binsh/ssl_client, scanelf | GPL-2.0-only: preserve copyright/GPL, corresponding program source and build/install scripts; use an actual-source delivery path, not an improvised offer | All recipe-listed source inputs and recipe files hash-verified; original code-header notices/common helper completeness need final check |
| FRR, iproute2 variants, libxtables | GPL-2.0-or-later: preserve per-file terms and selected combined-work license; include source/patch/build/install material | Verified source inputs/recipes; FRR COPYING is best-effort and its additional doc/licenses/custom documentation terms still need the final notice selection |
| Bash, Readline | GPL-3.0-or-later: GPLv3 conveyance/source and applicable notices | Verified sources/patches; GPLv3 texts copied. Actual vtysh NEEDED includes libreadline.so.8; select/document its combined-work license consistently with FRR's -or-later grant |
| libmnl | LGPL-2.1-or-later: library source, notice/license and applicable linked-work/relinking conditions, not automatically source for unrelated programs | Source/patch/recipe verified, original LGPL text copied; retain replaceable shared-library mechanism and assess the actual combination before final clearance |
| libelf | APK expression GPL-3.0-or-later AND (GPL-2.0-or-later OR LGPL-3.0-or-later): do not flatten | Source/recipe and three GNU license texts available; determine exact installed libelf file-level grant rather than applying tool/documentation terms by metadata alone |
| ca-certificates-bundle | MPL-2.0 AND MIT: preserve covered certdata source/notices and MIT material; source access for the covered part, not an automatic GPL obligation | Source input/recipe verified; certify certdata notice/header and generated-bundle provenance plus MIT script/material attribution |
| musl / musl-utils | musl MIT; utils MIT AND BSD-2-Clause AND GPL-2.0-or-later: separate installed utility components | Original COPYRIGHT copied; verify precise utilities/headers under the mixed expression. Include applicable copyleft utility source, not a blanket source obligation for MIT musl |
| libcap2 | BSD-3-Clause OR GPL-2.0-only | Full original License retained. Proposed permissive branch needs confirmation against actual libcap library files, not a silent OR collapse |
| zstd-libs | BSD-3-Clause OR GPL-2.0-or-later | Original BSD LICENSE retained. Proposed BSD path for the library remains subject to file-level confirmation; source collected voluntarily for notice extraction/reconstruction |
| c-ares, json-c, OpenSSL libs, ncurses variants, libyang, pcre2, tini, zlib | Respective MIT/Apache-2.0/X11/BSD-3-Clause-Clear/BSD/Zlib notice requirements | Original selected legal texts copied with upstream-member and stored hashes. Source archives were used to retrieve notices, not because permissive licensing inherently requires full-source delivery |
| alpine-keys / alpine-release | APK-declared MIT | Exact recipe/source files traced; explicit corresponding copyright/permission text or a supported determination of the generated data's applicable attribution still needs confirmation; do not invent a holder |

See [selected original legal texts and hashes](evidence/task0004-notice-texts.json)
and `licenses/third-party/`. Text normalization is documented; stored-file hashes
are distinct from the original archive-member hashes. This directory contains
third-party material, **not** MIT project-original code. Top-level legal files
alone are not asserted to cover every embedded file or linked-work condition.

## Itemized remaining source/notice/legal questions — category STOP

1. **Common build controls:** identify/retain any necessary Alpine abuild helper
   scripts/configuration not included in the 180 origin-directory files, or
   establish which external build tools fall outside the required source set.
   Recipe-listed inputs being complete is not full corresponding-source clearance.
2. **Alpine-generated data and cert bundle:** original MIT attributions for
   alpine-keys/alpine-release and MIT portions of ca-certificates; applicable
   MPL certdata header/text and generated-bundle source relationship. No legal
   text was fabricated to fill these gaps.
3. **Linked/alternative licensing:** actual [ELF NEEDED evidence](evidence/task0004-elf-linkage.json)
   shows GPL-2.0-only-declared libapk linked to libssl.so.3/libcrypto.so.3
   (Apache-2.0-declared OpenSSL). Is there an applicable upstream linking
   exception or other valid distribution basis? **This is a specific qualified
   license-review question, not a conclusion of incompatibility.** Likewise
   resolve vtysh/Readline combined-work selection, libelf's actual grant,
   libcap/zstd OR paths and musl-utils file-level attribution. Do not change FRR,
   distro, package versions or privilege management to conceal an unresolved term.
4. **Complete notice selection:** FRR doc/licenses and custom documentation
   terms, file-header copyrights and any relevant bundled exceptions/NOTICE
   must be mapped to final distributed files. Copied root texts are useful
   material, not automatic file-level compliance.
5. **Delivery acceptance:** the exact full archive, reconstruction instructions,
   project source at the eventually accepted MIT commit, recipient-access test,
   final bundle digest and retention/custodian binding are not finished.

The finite missing list above supersedes a vague request for a broad audit.
Verified artifacts are reusable; no new versions/builds or unlimited source
searches are requested. Stop this category for Owner/qualified review rather
than claiming an upstream hyperlink is a valid source offer.

## Recipient-access and retention proposal for Owner decision

Proposed convenience endpoint: versioned GitHub Release source assets in this
public repository, prominently linked beside the exact Docker Hub tag and in
image notices. Assets are **NOT PUBLISHED** and no final recipient URL exists.
Owner must designate a custodian and retention/backup budget for at least the
measured payload plus revisions. Keep exact source/notice bundles available
throughout binary availability and all longer applicable obligations; do not
silently delete old source when replacing an image tag.

The [GPLv2 download-distribution guidance](https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq.html)
and [GPLv3 section 6(d)](https://www.gnu.org/licenses/gpl-3.0.html) make the
actual access arrangement important. A cross-host Hub/GitHub link is proposed,
not declared compliant. A finite alternative for review is carrying the complete
reviewed compressed corresponding-source bundle **inside the same published
image**, alongside notices, with GitHub assets as an additional convenience.
That increases image size and changes digests but avoids depending solely on
a separate source host. Choose and verify the applicable licence fulfilment
path before a final artifact build; neither alternative is implemented here.
No written offer is issued. A written-offer alternative needs its own reviewed
conditions and durations, not a generic promise.
