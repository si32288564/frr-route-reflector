#!/usr/bin/env python3
"""Materialize only frozen Task 0004 inputs for a local, explicitly partial bundle.

No source execution/build/install, image launch, scanner or publication.
The old probes retained hashes, not payloads; existing matching files are reused.
"""
import concurrent.futures
import hashlib
import json
import pathlib
import shutil
import sys
import tarfile
import urllib.request

root = pathlib.Path(sys.argv[1]).resolve()
assert root.parent == pathlib.Path("/tmp") and root.name.startswith("frr-task0004-bundle.")
project = root / "staging/project"
manifest = json.loads((project / "docs/evidence/task0004-source-bundle-manifest.json").read_text())
free = shutil.disk_usage(root).free
required = 2 * (manifest["verified_input_bytes"] + manifest["verified_recipe_bytes"]) + 96 * 1024**2
assert free >= required + 192 * 1024**2, "STOP: insufficient packaging free space/reserve"
records = []


def sha(data):
    return hashlib.sha256(data).hexdigest()


def acquire(job):
    relative, item, kind = job
    dest = root / "staging" / relative
    assert not pathlib.PurePosixPath(relative).is_absolute() and ".." not in pathlib.PurePosixPath(relative).parts
    dest.parent.mkdir(parents=True, exist_ok=True)
    reused = dest.exists()
    if reused:
        data = dest.read_bytes()
        # Only this task-owned new workspace can contain incomplete prior writes.
        if len(data) != item["bytes"] or sha(data) != item["sha256"]:
            reused = False
    if not reused:
        assert item["url"].startswith(("https://distfiles.alpinelinux.org/", "https://raw.githubusercontent.com/alpinelinux/aports/"))
        with urllib.request.urlopen(item["url"], timeout=25) as response:
            data = response.read(item["bytes"] + 1)
    assert len(data) == item["bytes"] and sha(data) == item["sha256"], "STOP: frozen input hash/size mismatch: " + relative
    if kind == "input":
        assert hashlib.sha512(data).hexdigest() == item["expected_sha512"]
    else:
        assert hashlib.sha1(("blob " + str(len(data)) + "\0").encode() + data).hexdigest() == item["git_blob_sha1"]
    if not reused:
        dest.write_bytes(data)
    return {"path": relative, "sha256": sha(data), "bytes": len(data), "kind": kind,
            "url": item["url"], "reused": reused}


jobs = []
for origin in manifest["origins"]:
    base = "origins/" + origin["origin"] + "/" + origin["version"]
    for item in origin["source_inputs"]:
        jobs.append((base + "/inputs/" + item["name"], item, "input"))
    for item in origin["recipe_files"]:
        jobs.append((base + "/recipe/" + item["path"], item, "recipe"))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    records = list(pool.map(acquire, jobs))
assert sum(r["bytes"] for r in records) == 112063647
result = {"free_bytes_before": free, "required_payload_and_packaging_bytes": required,
          "reserve_bytes": 192 * 1024**2, "inputs": 173, "recipes": 180,
          "materialized_bytes": sum(r["bytes"] for r in records), "files": records,
          "source_cache": "Only existing frozen URLs/hashes; prior probes held payloads in memory, not on disk",
          "result": "PASS materialization only; not source/legal completeness"}
(root / "materialization.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({key: value for key, value in result.items() if key != "files"}))

# Enumerate bounded relevant review material without extracting upstream trees.
selection = {
    "alpine-baselayout": ["COPYING", "LICENSE"],
    "apk-tools": ["LICENSE", "COPYING", "README.md", "meson.build", "src/apk_crypto.h"],
    "ca-certificates": ["mozilla/certdata.txt", "debian/copyright", "COPYING", "LICENSE", "update-ca-certificates"],
    "elfutils": ["libelf/elf_begin.c", "libelf/elf_end.c", "libelf/README", "COPYING-LGPLV3", "COPYING-GPLV2"],
    "libcap": ["License", "libcap/cap_alloc.c", "libcap/include/sys/capability.h"],
    "zstd": ["LICENSE", "COPYING", "lib/zstd.h", "lib/common/xxhash.h"],
    "musl": ["COPYRIGHT", "tools/ldd", "tools/ldd.sh"],
    "frr": ["COPYING", "vtysh/vtysh.c", "doc/COPYING", "doc/README", "lib/version.h"],
}
review = []
notices = []
for origin in manifest["origins"]:
    for source in origin["source_inputs"]:
        path = root / "staging/origins" / origin["origin"] / origin["version"] / "inputs" / source["name"]
        try:
            archive = tarfile.open(path)
        except tarfile.TarError:
            continue
        with archive:
            for member in archive:
                rel = member.name.split("/", 1)[-1]
                wanted = rel in selection.get(origin["origin"], [])
                legal = any(n["path"] == member.name for n in source.get("notice_members", []))
                if not member.isfile() or member.size > 256 * 1024 or not (wanted or legal):
                    continue
                data = archive.extractfile(member).read()
                record = {"origin": origin["origin"], "input": source["name"], "member": member.name,
                          "sha256": sha(data), "bytes": len(data)}
                if legal:
                    dest = root / "staging/notices/original" / origin["origin"] / source["name"] / member.name
                    assert not pathlib.PurePosixPath(member.name).is_absolute() and ".." not in pathlib.PurePosixPath(member.name).parts
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(data)  # Original bytes, no normalization.
                    record["bundle_path"] = str(dest.relative_to(root / "staging"))
                    notices.append(dict(record))
                if wanted:
                    # Selected headers/texts only, not bulk source publication to GitHub.
                    record["text"] = data.decode("utf-8", errors="replace")[:24000]
                    review.append(record)
(root / "review-material.json").write_text(json.dumps(review, indent=2) + "\n")
(root / "notice-members.json").write_text(json.dumps(notices, indent=2) + "\n")
print(json.dumps({"selected_review_members": len(review), "original_notice_members": len(notices)}))
