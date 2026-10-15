#!/usr/bin/env python3
"""Bounded selected license facts from the frozen local source set; no execution."""
import hashlib
import json
import pathlib
import sys
import tarfile
import urllib.request
import urllib.error

root = pathlib.Path(sys.argv[1]).resolve()
assert root.name.startswith("frr-task0004-bundle.") and root.parent == pathlib.Path("/tmp")
staging = root / "staging"
manifest = json.loads((staging / "project/docs/evidence/task0004-source-bundle-manifest.json").read_text())
facts, extras, gaps = [], [], []
selected = {
    "ca-certificates": ["certdata.txt", "update-ca.c", "c_rehash.c", "split-ca-bundle.sh", "Makefile", "README"],
    "elfutils": ["libelf/elf_begin.c", "libelf/elf_end.c"],
    "libcap": ["License", "psx/License", "libcap/cap_alloc.c"],
    "zstd": ["lib/zstd.h", "lib/common/xxhash.h"],
    "frr": ["COPYING", "vtysh/vtysh.c", "doc/user/index.rst", "yang/ietf-interfaces.yang"],
    "apk-tools": ["LICENSE", "src/apk_crypto.h", "src/crypto_openssl.c", "meson.build"],
}
for origin in manifest["origins"]:
    base = staging / "origins" / origin["origin"] / origin["version"]
    if origin["origin"] in ("alpine-base", "alpine-keys"):
        url = "https://raw.githubusercontent.com/alpinelinux/aports/" + origin["aports_commit"] + "/COPYING"
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                data = response.read(32768)
        except urllib.error.HTTPError as error:
            gaps.append({"origin": origin["origin"], "url": url, "http": error.code,
                         "gap": "No root COPYING at fixed recipe commit; generated-data attribution unresolved"})
        else:
            dest = staging / "notices/additional" / (origin["origin"] + "-aports-COPYING.txt")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            extras.append({"origin": origin["origin"], "url": url, "sha256": hashlib.sha256(data).hexdigest(),
                           "bytes": len(data), "bundle_path": str(dest.relative_to(staging))})
    if origin["origin"] == "musl":
        for name in ("getconf.c", "getent.c", "iconv.c", "ldconfig"):
            data = (base / "inputs" / name).read_bytes()
            dest = staging / "notices/additional/musl" / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            extras.append({"origin": "musl", "sha256": hashlib.sha256(data).hexdigest(),
                           "bytes": len(data), "bundle_path": str(dest.relative_to(staging))})
            facts.append({"origin": "musl", "path": str((base / "inputs" / name).relative_to(staging)),
                          "sha256": hashlib.sha256(data).hexdigest(), "header": data.decode()[:2200]})
    for source in origin["source_inputs"]:
        if origin["origin"] not in selected:
            continue
        try:
            archive = tarfile.open(base / "inputs" / source["name"])
        except tarfile.TarError:
            continue
        with archive:
            for member in archive:
                if not member.isfile():
                    continue
                rel = member.name.split("/", 1)[-1]
                wanted = rel in selected[origin["origin"]]
                extra = origin["origin"] == "frr" and rel.startswith("doc/licenses/")
                if not (wanted or extra):
                    continue
                assert member.size < 4 * 1024**2
                data = archive.extractfile(member).read()
                fact = {"origin": origin["origin"], "input": source["name"], "member": member.name,
                        "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                if wanted:
                    facts.append(dict(fact, header=data.decode(errors="replace")[:2200]))
                if extra or (origin["origin"] in ("ca-certificates", "frr", "elfutils", "libcap", "zstd") and wanted):
                    dest = staging / "notices/additional" / origin["origin"] / member.name
                    assert ".." not in pathlib.PurePosixPath(member.name).parts
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)
                    extras.append(dict(fact, bundle_path=str(dest.relative_to(staging))))

url = "https://www.mozilla.org/media/MPL/2.0/index.txt"
with urllib.request.urlopen(url, timeout=20) as response:
    data = response.read(65536)
assert data.startswith(b"Mozilla Public License")
dest = staging / "notices/additional/MPL-2.0.txt"
dest.write_bytes(data)
extras.append({"origin": "ca-certificates", "url": url, "sha256": hashlib.sha256(data).hexdigest(),
               "bytes": len(data), "bundle_path": str(dest.relative_to(staging))})
(root / "license-facts.json").write_text(json.dumps(facts, indent=2) + "\n")
(root / "additional-notices.json").write_text(json.dumps(extras, indent=2) + "\n")
(root / "notice-gaps.json").write_text(json.dumps(gaps, indent=2) + "\n")
print(json.dumps({"selected_facts": len(facts), "additional_notice_files": len(extras), "attribution_gaps": len(gaps)}))
