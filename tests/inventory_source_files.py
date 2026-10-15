#!/usr/bin/env python3
"""APK-owned installed paths from existing frozen exports; no image execution."""
import hashlib
import json
import pathlib
import sys
import tarfile

inventory = json.loads(pathlib.Path(sys.argv[1]).read_text())["images"]
exports = pathlib.Path(sys.argv[2])
result = {"method": "APK F/R ownership + final-layer path hashes; no executable launch", "images": []}
for image in inventory:
    arch = image["architecture"]
    files, installed = {}, None
    with tarfile.open(exports / (arch + ".tar")) as archive:
        manifests = json.load(archive.extractfile("manifest.json"))
        assert len(manifests) == 1
        entry = manifests[0]
        assert hashlib.sha256(archive.extractfile(entry["Config"]).read()).hexdigest() == image["config_sha256"]
        for layer_name in entry["Layers"]:
            with tarfile.open(fileobj=archive.extractfile(layer_name), mode="r|*") as layer:
                for member in layer:
                    name = member.name.removeprefix("./").lstrip("/")
                    path = pathlib.PurePosixPath(name)
                    if path.name == ".wh..wh..opq":
                        files = {p: f for p, f in files.items() if not p.startswith(str(path.parent) + "/")}
                    elif path.name.startswith(".wh."):
                        files.pop(str(path.parent / path.name[4:]), None)
                    elif member.isfile():
                        data = layer.extractfile(member).read()
                        files[name] = {"path": name, "kind": "file", "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}
                        if name == "lib/apk/db/installed":
                            installed = data.decode()
                    elif member.issym() or member.islnk():
                        files[name] = {"path": name, "kind": "symlink" if member.issym() else "hardlink",
                                       "link_target_sha256": hashlib.sha256(member.linkname.encode()).hexdigest()}
    assert installed
    packages = []
    owned = set()
    for record in installed.strip().split("\n\n"):
        name = next(line[2:] for line in record.splitlines() if line.startswith("P:"))
        pkg = next(p for p in image["packages"] if p["name"] == name)
        paths, directory = [], ""
        for line in record.splitlines():
            if line.startswith("F:"):
                directory = line[2:]
            elif line.startswith("R:"):
                path = str(pathlib.PurePosixPath(directory) / line[2:])
                if path in files:
                    paths.append(files[path])
                    owned.add(path)
        packages.append({"name": name, "version": pkg["version"], "origin": pkg["origin"],
                         "declared_license": pkg["declared_license"], "files": sorted(paths, key=lambda f: f["path"])})
    assert len(packages) == 35
    result["images"].append({"architecture": arch, "local_id": image["docker_id"], "config_sha256": image["config_sha256"],
                             "packages": sorted(packages, key=lambda p: p["name"]),
                             "non_apk_owned_paths": [files[p] for p in sorted(set(files) - owned)]})
out = pathlib.Path(sys.argv[3])
assert out.parent.name.startswith("frr-task0004-bundle.")
out.write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"images": [{"architecture": i["architecture"],
                               "package_paths": sum(len(p["files"]) for p in i["packages"]),
                               "non_apk_owned_paths": len(i["non_apk_owned_paths"])} for i in result["images"]]}))
