# Third-party notices — prepublication inventory (NOT compliance clearance)

The root [MIT LICENSE](LICENSE) applies only to original project material.
The Alpine/FRR image is an aggregation of separately licensed components, not
an entirely MIT-licensed image. No third-party code is relicensed here.
Owner confirmed original-work rights and public attribution in
[Issue #12](https://github.com/si32288564/frr-route-reflector/issues/12#issuecomment-6191673478).

**Publication STOP:** this inventory does not yet include all original copyright
notices/license texts or complete, recipient-accessible corresponding source.
It is NOT a substitute for those materials and must not be presented as a
finished notice bundle. Exact third-party copyright attributions remain
NOT VERIFIED; package upstream links identify projects, not confirmed legal
copyright holders. Do not invent attribution names from package maintainers.

## Exact bundled packages

Observed directly from Docker-save layers of both existing local candidate images:

- AMD64 manifest/Docker ID: `sha256:dbc288be32f2833223262801f287d4ba1be4594059a9a06001d31b963e2d428a`.
- ARM64 manifest/Docker ID: `sha256:dea86108c2812d9891674e0291af3b59872925e6c462e189a08acf0b3f61f096`.

Each row represents two installed packages: architecture **x86_64** in AMD64
and **aarch64** in ARM64. All 35 names, versions, declared expressions,
upstream URLs, origins and aports commits match across architectures.
APK checksums and binaries are architecture-specific. Full metadata is in
[the image inventory](docs/evidence/task0004-image-inventory.json);
[the APK CycloneDX inventory](docs/evidence/task0004-apk-sbom.cdx.json)
contains 70 component instances. This is package-manager-derived SBOM content,
not a scanner-generated or independently verified bill of all embedded code.
CycloneDX schema validation has NOT RUN; JSON and component consistency are tested.

License expressions below are verbatim APK declarations, including AND/OR and
parentheses. They are not file-level license conclusions. Applicable exceptions,
additional terms, embedded code and combined-binary obligations require source
inspection before redistribution. Recipe URLs are fixed to the installed APK's
aports commit, not a floating branch.

| Package | Version (both arches) | APK-declared expression | Upstream / fixed recipe | Required review/fulfilment categories |
|---|---|---|---|---|
| alpine-baselayout | 3.7.2-r1 | `GPL-2.0-only` | [upstream](https://gitlab.alpinelinux.org/alpine/aports/-/tree/master/main/alpine-baselayout) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/60a7585bbab2fa0f762504eb617dbca90216e31f/main/alpine-baselayout/APKBUILD) | G2 |
| alpine-baselayout-data | 3.7.2-r1 | `GPL-2.0-only` | [upstream](https://gitlab.alpinelinux.org/alpine/aports/-/tree/master/main/alpine-baselayout) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/60a7585bbab2fa0f762504eb617dbca90216e31f/main/alpine-baselayout/APKBUILD) | G2 |
| alpine-keys | 2.6-r0 | `MIT` | [upstream](https://alpinelinux.org) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/b9f23becced4d7b3ccc0fa0f28530243ccd314a0/main/alpine-keys/APKBUILD) | NOTICE |
| alpine-release | 3.24.2-r0 | `MIT` | [upstream](https://alpinelinux.org) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/d9d560d5de74ff9a7a73f3c903d6f126a0bf3142/main/alpine-base/APKBUILD) | NOTICE |
| apk-tools | 3.0.8-r0 | `GPL-2.0-only` | [upstream](https://gitlab.alpinelinux.org/alpine/apk-tools) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/4588b452722bd4800efdc6cce4f6e980e02a997f/main/apk-tools/APKBUILD) | G2 |
| bash | 5.3.9-r1 | `GPL-3.0-or-later` | [upstream](https://www.gnu.org/software/bash/bash.html) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/1522c3193610902d8493f9790a2755c11f21f26d/main/bash/APKBUILD) | G3 |
| busybox | 1.37.0-r31 | `GPL-2.0-only` | [upstream](https://busybox.net/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/c3ef5d10e6ef6528852c51f0564963e2f8c1be19/main/busybox/APKBUILD) | G2 |
| busybox-binsh | 1.37.0-r31 | `GPL-2.0-only` | [upstream](https://busybox.net/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/c3ef5d10e6ef6528852c51f0564963e2f8c1be19/main/busybox/APKBUILD) | G2 |
| c-ares | 1.34.8-r0 | `MIT` | [upstream](https://c-ares.org/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/138a6bf9dea5974644e48fef4826b7c474f2f7d8/main/c-ares/APKBUILD) | NOTICE |
| ca-certificates-bundle | 20260909-r0 | `MPL-2.0 AND MIT` | [upstream](https://www.mozilla.org/en-US/about/governance/policies/security-group/certs/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/eb7078df3a16d666e8f7723f94bb92e00d4b9236/main/ca-certificates/APKBUILD) | MPL, NOTICE |
| frr | 10.6.1-r0 | `GPL-2.0-or-later` | [upstream](https://frrouting.org/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/23a7c9f1a27473a1a8a09ad3433d4a7a5b0fb62c/community/frr/APKBUILD) | G2 |
| iproute2 | 7.0.0-r0 | `GPL-2.0-or-later` | [upstream](https://wiki.linuxfoundation.org/networking/iproute2) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/3ee752ad0c8445c8105177cd5cebdd730789bcd8/main/iproute2/APKBUILD) | G2 |
| iproute2-minimal | 7.0.0-r0 | `GPL-2.0-or-later` | [upstream](https://wiki.linuxfoundation.org/networking/iproute2) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/3ee752ad0c8445c8105177cd5cebdd730789bcd8/main/iproute2/APKBUILD) | G2 |
| iproute2-ss | 7.0.0-r0 | `GPL-2.0-or-later` | [upstream](https://wiki.linuxfoundation.org/networking/iproute2) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/3ee752ad0c8445c8105177cd5cebdd730789bcd8/main/iproute2/APKBUILD) | G2 |
| iproute2-tc | 7.0.0-r0 | `GPL-2.0-or-later` | [upstream](https://wiki.linuxfoundation.org/networking/iproute2) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/3ee752ad0c8445c8105177cd5cebdd730789bcd8/main/iproute2/APKBUILD) | G2 |
| json-c | 0.18-r1 | `MIT` | [upstream](https://github.com/json-c/json-c/wiki) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/8e0faa63c91abd41feb359ce5fe4299a88a57ef1/main/json-c/APKBUILD) | NOTICE |
| libapk | 3.0.8-r0 | `GPL-2.0-only` | [upstream](https://gitlab.alpinelinux.org/alpine/apk-tools) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/4588b452722bd4800efdc6cce4f6e980e02a997f/main/apk-tools/APKBUILD) | G2 |
| libcap2 | 2.78-r0 | `BSD-3-Clause OR GPL-2.0-only` | [upstream](https://sites.google.com/site/fullycapable/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/0c35848136c4c16a1b1672cb812efa88fffef1c2/main/libcap/APKBUILD) | OR, G2, NOTICE |
| libcrypto3 | 3.5.8-r0 | `Apache-2.0` | [upstream](https://www.openssl.org/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/013edf8b29199933e8ea34dde460b5584b979042/main/openssl/APKBUILD) | NOTICE |
| libelf | 0.195-r0 | `GPL-3.0-or-later AND ( GPL-2.0-or-later OR LGPL-3.0-or-later )` | [upstream](https://sourceware.org/elfutils/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/8f13294206888f3dd44ed74a8eb3dd9934499e81/main/elfutils/APKBUILD) | OR, G2, G3, L3 |
| libmnl | 1.0.5-r2 | `LGPL-2.1-or-later` | [upstream](https://www.netfilter.org/projects/libmnl/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/fc95c59998285564fbcb0bfb2443898c62e10171/main/libmnl/APKBUILD) | L21 |
| libncursesw | 6.6_p20260516-r0 | `X11` | [upstream](https://invisible-island.net/ncurses/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/2cee8a7328d061418336ad327b512d96bcd7bc5e/main/ncurses/APKBUILD) | NOTICE |
| libssl3 | 3.5.8-r0 | `Apache-2.0` | [upstream](https://www.openssl.org/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/013edf8b29199933e8ea34dde460b5584b979042/main/openssl/APKBUILD) | NOTICE |
| libxtables | 1.8.13-r0 | `GPL-2.0-or-later` | [upstream](https://www.netfilter.org/projects/iptables/index.html) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/8848fb97f5ec1aa887b836cf412d88eaabe312b6/main/iptables/APKBUILD) | G2 |
| libyang | 3.13.6-r1 | `BSD-3-Clause-Clear` | [upstream](https://github.com/CESNET/libyang) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/a9e2a2dc46f377eb25884f7fea9834492de7f518/community/libyang/APKBUILD) | NOTICE |
| musl | 1.2.6-r2 | `MIT` | [upstream](https://musl.libc.org/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/f5640d3a10f664c9119720c60515265d3d6f6d01/main/musl/APKBUILD) | NOTICE |
| musl-utils | 1.2.6-r2 | `MIT AND BSD-2-Clause AND GPL-2.0-or-later` | [upstream](https://musl.libc.org/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/f5640d3a10f664c9119720c60515265d3d6f6d01/main/musl/APKBUILD) | G2, NOTICE |
| ncurses-terminfo-base | 6.6_p20260516-r0 | `X11` | [upstream](https://invisible-island.net/ncurses/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/2cee8a7328d061418336ad327b512d96bcd7bc5e/main/ncurses/APKBUILD) | NOTICE |
| pcre2 | 10.49-r0 | `BSD-3-Clause` | [upstream](https://pcre.org/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/3d497cbb3217749c4fb85f90f3b6f7908b0c1f95/main/pcre2/APKBUILD) | NOTICE |
| readline | 8.3.3-r1 | `GPL-3.0-or-later` | [upstream](https://tiswww.cwru.edu/php/chet/readline/rltop.html) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/a854c03acdac188901fb012f7acbee70a36e8041/main/readline/APKBUILD) | G3 |
| scanelf | 1.3.9-r1 | `GPL-2.0-only` | [upstream](https://wiki.gentoo.org/wiki/Hardened/PaX_Utilities) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/c61801eeacb3ffcd9c2025b09e402153bb93fb39/main/pax-utils/APKBUILD) | G2 |
| ssl_client | 1.37.0-r31 | `GPL-2.0-only` | [upstream](https://busybox.net/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/c3ef5d10e6ef6528852c51f0564963e2f8c1be19/main/busybox/APKBUILD) | G2 |
| tini | 0.19.0-r3 | `MIT` | [upstream](https://github.com/krallin/tini) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/494a61016db8d643534788c47f074935ef2e6035/community/tini/APKBUILD) | NOTICE |
| zlib | 1.3.2-r0 | `Zlib` | [upstream](https://zlib.net/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/f248b33b5943c7dc69bf691031d7612ab2e8ed93/main/zlib/APKBUILD) | NOTICE |
| zstd-libs | 1.5.7-r2 | `BSD-3-Clause OR GPL-2.0-or-later` | [upstream](https://facebook.github.io/zstd/) / [recipe](https://raw.githubusercontent.com/alpinelinux/aports/3c6e2ee2b16f403d53eab39c4426eb61f003c322/main/zstd/APKBUILD) | OR, G2, NOTICE |

## Required notices, texts and source obligations

These are conservative review categories, **not legal approval**. All rows
require the original applicable license/copyright notices from the exact source,
plus package-level modifications/build/install scripts where required. Preserve
the full expression; do not collapse AND into OR or select an OR branch silently.

- **NOTICE:** retain applicable MIT/BSD/X11/Zlib notices and license terms;
  Apache-2.0 additionally needs its license, applicable NOTICE contents and
  modification attribution. BSD-3-Clause-Clear's terms must not be replaced by
  ordinary BSD-3-Clause. Required exact texts/notices are NOT VERIFIED.
- **G2:** GPLv2-compatible fulfilment must include complete corresponding source,
  build/install scripts and distro modifications, plus the GPL and notices.
  GPL-2.0-only and -or-later are distinct. See [GPLv2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html)
  and the [FSF download-distribution FAQ](https://www.gnu.org/licenses/old-licenses/gpl-2.0-faq.html).
- **G3:** GPLv3 adds its corresponding-source/conveying requirements; plan
  equivalent source access with clear directions alongside object-code access,
  under the applicable section 6 option. Do not assume a GPLv2-style generic
  written offer suffices. See [GPLv3](https://www.gnu.org/licenses/gpl.en.html).
- **L21 / L3:** provide applicable LGPL notices/text and library source;
  assess linked-work modification/relinking, reverse-engineering permissions
  and the chosen shared-library mechanism. Dynamic linking alone is not a
  compliance determination. See [LGPL 2.1](https://www.gnu.org/licenses/old-licenses/lgpl-2.1-standalone.html)
  and [LGPL 3](https://www.gnu.org/licenses/lgpl.html).
- **MPL:** preserve required notices and make the covered source form available
  with recipient directions; identify the actual covered files, not just the
  bundle's metadata. See [MPL 2.0 sections 3.1–3.2](https://www.mozilla.org/en-US/MPL/2.0/).
- **OR:** determine and document the applicable distribution choice from exact
  upstream terms. The table lists potentially relevant branches conservatively,
  not a claim all mutually alternative branches must be selected together.

FRR's [10.6.1 COPYING](https://raw.githubusercontent.com/FRRouting/frr/frr-10.6.1/COPYING)
describes mixed per-file SPDX licensing and qualifies its GPLv2-or-later
combined-binary conclusion as best effort, not a legal guarantee; documentation
has additional historical terms. Neither the frr APK license field nor this
project's MIT license resolves that review.

All 25 origin recipes were reachable at fixed commits with matching pkgver/pkgrel.
This establishes traceability, not complete source delivery. See
[source probes](docs/evidence/task0004-source-recipe-probes.json) and
[the delivery plan / remaining gates](docs/publishing-preflight.md).
No installed-path names matching license/COPYING/copyright/NOTICE were observed
by the limited image-layer name heuristic; licenses might use other names or
be embedded. Do not infer their absence solely from this heuristic. A finished
publication candidate must carry/provide the required texts and notices.
