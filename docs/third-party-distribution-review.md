# Third-party distribution preparation — finite review handoff

Codexによる報告:

2026-10-16 JST. Authority: [Issue #12 continuation](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6195095706).
This is a reviewable **partial local package**, not permission to distribute.
Original-work MIT rights are Owner-confirmed; third-party terms are unchanged.
**CVE scan NOT RUN — Owner explicitly omitted.** Vulnerabilities are unknown;
scanner cancellation is not acceptance of an unscreened public release.

## Per-origin final preparation matrix

The [machine matrix](evidence/task0004-origin-distribution-matrix.json) records
every installed APK-owned file path, exact local source paths/SHA256, pinned
recipe identity/count, original notice paths and a finite review result per
origin. Complete architecture-specific installed file hashes are inside the
archive at `metadata/distributed-files.json`; all staged file hashes are in
`MANIFEST.json`. The public matrix links those finite records rather than
publishing binary payloads or several thousand duplicate metadata lines.

Below, file count is the union of APK-owned final paths across architectures,
not a count of all embedded code or generated files. Material gate is **PASS
for the recorded inputs/recipes**, not full legal clearance. All rows retain
the final notice-placement/delivery and applicable external-helper review gate;
the specifically unresolved origins are described below. Permissive origins'
source is included voluntarily for traceability, not a blanket source duty.

| Origin | Distributed APKs | File paths | Inputs/recipe files | Unchanged APK license expression(s) |
|---|---|---:|---:|---|
| alpine-baselayout | alpine-baselayout, alpine-baselayout-data | 28 | 14/17 | `GPL-2.0-only` |
| alpine-keys | alpine-keys | 43 | 18/19 | `MIT` |
| alpine-base | alpine-release | 5 | 0/1 | `MIT` |
| apk-tools | apk-tools, libapk | 2 | 2/2 | `GPL-2.0-only` |
| bash | bash | 43 | 13/7 | `GPL-3.0-or-later` |
| busybox | busybox, busybox-binsh, ssl_client | 9 | 75/80 | `GPL-2.0-only` |
| c-ares | c-ares | 2 | 1/1 | `MIT` |
| ca-certificates | ca-certificates-bundle | 4 | 1/3 | `MPL-2.0 AND MIT` |
| frr | frr | 103 | 3/4 | `GPL-2.0-or-later` |
| iproute2 | iproute2, iproute2-minimal, iproute2-ss, iproute2-tc | 28 | 1/2 | `GPL-2.0-or-later` |
| json-c | json-c | 2 | 2/2 | `MIT` |
| libcap | libcap2 | 4 | 1/1 | `BSD-3-Clause OR GPL-2.0-only` |
| openssl | libcrypto3, libssl3 | 11 | 2/3 | `Apache-2.0` |
| elfutils | libelf | 2 | 5/5 | `GPL-3.0-or-later AND ( GPL-2.0-or-later OR LGPL-3.0-or-later )` |
| libmnl | libmnl | 2 | 2/2 | `LGPL-2.1-or-later` |
| ncurses | libncursesw, ncurses-terminfo-base | 43 | 2/2 | `X11` |
| iptables | libxtables | 2 | 7/8 | `GPL-2.0-or-later` |
| libyang | libyang | 12 | 1/1 | `BSD-3-Clause-Clear` |
| musl | musl, musl-utils | 9 | 11/11 | `MIT`; `MIT AND BSD-2-Clause AND GPL-2.0-or-later` |
| pcre2 | pcre2 | 4 | 1/1 | `BSD-3-Clause` |
| readline | readline | 3 | 6/3 | `GPL-3.0-or-later` |
| pax-utils | scanelf | 1 | 1/1 | `GPL-2.0-only` |
| tini | tini | 1 | 2/2 | `MIT` |
| zlib | zlib | 2 | 1/1 | `Zlib` |
| zstd | zstd-libs | 2 | 1/1 | `BSD-3-Clause OR GPL-2.0-or-later` |

Actual file evidence: 363 APK-owned paths on AMD64 and 362 on ARM64, plus 318
non-APK-recorded final paths on each. The latter include package-created BusyBox
applet links, runtime/base-generated metadata and original project additions;
not being in APK F/R records does not mean separate unknown software. Their
hashes/link-target hashes are retained, not their config/log contents. The
ownership method is not a source-to-binary reproduction claim. Project
`etc/frr/daemons` overrides the package's file and must not be mistaken for
pristine upstream config. Original upstream input archives and the recorded
modifications are preserved separately. No daemon/target program was run.

## Narrow issues resolved as source/notice evidence

- **musl-utils:** exact frozen APKBUILD generates `/usr/bin/ldd`; `getconf.c`
  and `getent.c` carry NetBSD BSD-2-Clause notices; `iconv.c` identifies Rich
  Felker and GPLv2-or-later. `ldconfig` is an Alpine recipe input calling scanelf,
  not musl's MIT libc source. Original utility files/headers and musl COPYRIGHT
  are included; the wrapper's missing explicit attribution is retained below.
- **libelf:** only `libelf-0.195.so`/its symlink are installed, not elfutils
  GPLv3 command-line tools. Selected `libelf/elf_begin.c` and `elf_end.c` grants
  expressly permit LGPLv3-or-later **or** GPLv2-or-later. Proposed library path:
  GPLv2-or-later with full source. Keep the APK's broader AND/OR metadata and
  all three original texts; selected headers are not an exhaustive linked-work
  legal opinion or permission to flatten package metadata.
- **libcap/psx and zstd:** installed libraries identified. libcap root `License`
  and `psx/License` expressly offer BSD-3-Clause OR GPL-2.0-only; zstd library
  and bundled xxhash headers explicitly offer the BSD/GPL alternative. Proposed
  BSD branches are grounded in those grants, with original full notices and
  copyright-bearing files retained. Do not silently rewrite upstream expressions.
- **FRR/vtysh/Readline:** `vtysh.c` is GPL-2.0-or-later; recorded NEEDED includes
  `libreadline.so.8`, whose package is GPL-3.0-or-later. A GPLv3-compatible
  vtysh/Readline distribution path is proposed, not an inferred GPLv2-only grant.
  Full FRR source, its nine `doc/licenses` texts and original manual copyright/
  permission in `doc/user/index.rst` are retained. Installed FRR paths contain
  binaries, scripts/config and YANG modules, with no manual paths observed;
  disabled daemon binaries still count as distributed. The unchanged source
  archive also includes documentation, so its custom terms remain preserved.
  FRR COPYING's best-effort qualification is not converted into legal PASS.
- **Mozilla bundle:** `certdata.txt` carries MPL 2.0; its exact 1,375,050 bytes,
  hash, Makefile and original MPL text are included. Installed package is only
  the certificate bundle/links, not MIT `c_rehash` or `update-ca` binaries.
  `c_rehash.c` identifies Timo Teräs/MIT and the conversion/split controls are
  preserved. Do not claim that every MIT-labelled tool is actually in this
  image or that generator license alone determines all generated output rights.

Exact selected file hashes and notice locations are in
[23 source facts / 29 additional materials](evidence/task0004-license-facts.json).
The archive additionally contains **52 original unnormalized legal members**
from already verified input archives and the historical **24 separately
normalized texts** in project material. These counts describe collected material,
not 81 independently complete licenses or a whole-image legal audit.

## Small remaining category STOP list

1. **Attribution:** alpine-keys public/generated key data and alpine-release
   generated release strings are traced to their exact inputs/APKBUILD, but
   package MIT metadata does not establish a genuine copyright/permission text
   for them. Fixed-commit root COPYING probes returned 404 (recorded, not an
   assertion that no applicable license exists). The short Alpine `ldconfig`
   wrapper likewise has no explicit grant/header in the checked input. No
   holder or license text is fabricated. Confirm the upstream attribution/basis
   for these three concrete materials before final notice selection.
2. **Applicable build helpers:** all 180 origin-directory files, patch/install
   inputs and upstream build/install controls are present. Exact original
   external abuild helper/toolchain revisions were not captured; confirm any
   actually required helper binding, or the applicable general-purpose-tool
   exclusion. This is a bounded missing binding, not a requirement to collect
   sources for every compiler/system tool or to rerun all source probes.
3. **One precise qualified legal question — libapk/OpenSSL:** for packaged
   apk-tools/libapk **3.0.8-r0**, `usr/lib/libapk.so.3.0.0` in both images has
   NEEDED `libssl.so.3` and `libcrypto.so.3` (**OpenSSL 3.5.8-r0**, Apache-2.0).
   Exact apk-tools source LICENSE is GPLv2 and `src/apk_crypto.h` explicitly
   GPL-2.0-only; `src/crypto_openssl.c` includes OpenSSL APIs and Meson selects
   the OpenSSL dependency. The recorded material establishes no verified
   linking exception. **What verifiable exception or other valid distribution
   basis permits conveying this exact combination, and what accompanying
   terms must we fulfil?** NEEDED alone proves neither incompatibility nor
   compliance; absence of an exception in selected material is not a global
   legal absence proof. Do not change FRR/packages to hide this question.
4. **Delivery/release binding:** approve notice placement/access and a suitable
   source-download mode, expressly accept Owner custody/retention, and bind a
   complete package to the eventually accepted source and final distributable
   bits. Current project binding is provisional. Public download is NOT RUN;
   local image/config IDs are not a multiarch registry index digest.

These narrow items keep **source/legal redistribution clearance BLOCKED**;
other preparation proceeds. No further source version search, scanner effort,
new architecture or generic compliance machinery is requested. See
[real local archive result](source-bundle-plan.md) and
[recipient/reconstruction and delivery proposal](source-bundle-reconstruction.md).

## Go/no-go and review request

| Gate | Disposition |
|---|---|
| Original material MIT / Owner copyright authority | Confirmed; PR remains an unmerged proposal |
| 35×2 packages → 25 origins / recorded source+recipe material | PASS preparation, bounded to recorded inputs |
| Local staging archive, file manifest, checksum, stream validation | PASS technical artifact; **partial**, not recipient-ready legal clearance |
| Final source/legal fulfilment / recipient access and stewardship | BLOCKED by four finite categories above |
| CVE scan | **NOT RUN — Owner explicitly omitted**, vulnerabilities unknown |
| Native AMD64 FRR; Kubernetes G-3/routing/non-transit | NOT RUN; opt-in SYS_ADMIN is still lab-only |
| Exact public tag/bits/release approval | NOT AUTHORIZED; `v0.1.0-lab.1` remains proposed |
| Docker Hub Push / GitHub Release / main merge / Kubernetes changes | NOT RUN, forbidden |

Request Chat/Owner review of this finite preparation package in existing Draft
PR #14. No claim of complete redistribution/security/runtime acceptance is made.
