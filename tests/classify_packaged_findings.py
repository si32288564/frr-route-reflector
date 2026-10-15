"""Finite offline comparison of recorded candidates to official Alpine APKs.

Downloads data only over HTTPS; never executes packages or prints matching bytes.
Use from repository root with the frozen Task 0004 inventory available.
"""
import hashlib
import io
import json
import pathlib
import re
import subprocess
import tarfile
import urllib.request

from prepublish_inventory import PATTERNS


def download(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read(32 * 1024 * 1024 + 1)
        assert len(data) <= 32 * 1024 * 1024
        return data


def files_from_apk(data, paths):
    # APK v2 consists of concatenated gzip/tar streams; skip tar zero blocks.
    result = {}
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz", ignore_zeros=True) as archive:
        for member in archive:
            path = member.name.removeprefix("./").lstrip("/")
            if path in paths and member.isfile():
                result[path] = archive.extractfile(member).read()
    return result


inventory = json.loads(pathlib.Path("docs/evidence/task0004-image-inventory.json").read_text())
results = []
for image in inventory["images"]:
    actual = json.loads(subprocess.check_output(["docker", "image", "inspect", image["image"]]))[0]
    assert actual["Id"] == image["docker_id"]
    paths = {location["path"] for location in image["disclosure_locations"]}
    image_files = {}
    saved = subprocess.run(["docker", "save", image["image"]], capture_output=True, check=True, timeout=90).stdout
    with tarfile.open(fileobj=io.BytesIO(saved)) as archive:
        manifest = json.load(archive.extractfile("manifest.json"))[0]
        for layer_name in manifest["Layers"]:
            with tarfile.open(fileobj=archive.extractfile(layer_name), mode="r|*") as layer:
                for member in layer:
                    path = member.name.removeprefix("./").lstrip("/")
                    if path in paths and member.isfile():
                        image_files[path] = layer.extractfile(member).read()
    for package_name, repository in [("apk-tools", "main"), ("frr", "community")]:
        package = next(p for p in image["packages"] if p["name"] == package_name)
        owned_paths = {p for p in paths if (p == "sbin/apk") == (package_name == "apk-tools")}
        url = "https://dl-cdn.alpinelinux.org/alpine/v3.24/" + repository + "/" + package["architecture"] + "/" + package_name + "-" + package["version"] + ".apk"
        data = download(url)
        official_files = files_from_apk(data, owned_paths)
        assert set(official_files) == owned_paths
        comparisons = []
        for path in sorted(owned_paths):
            actual_bytes, official_bytes = image_files[path], official_files[path]
            same = actual_bytes == official_bytes
            matches = {label: len(re.findall(pattern, actual_bytes)) for label, pattern in PATTERNS.items()}
            comparisons.append({"path": path, "image_sha256": hashlib.sha256(actual_bytes).hexdigest(),
                                "official_sha256": hashlib.sha256(official_bytes).hexdigest(),
                                "byte_equal": same, "candidate_counts": matches,
                                "classification": "unchanged official Alpine binary static content; not project-added confidential data" if same else "UNRESOLVED: binary differs"})
        results.append({"architecture": image["architecture"], "image_id": actual["Id"],
                        "package": package_name, "version": package["version"],
                        "official_url": url, "download_sha256": hashlib.sha256(data).hexdigest(),
                        "package_signature_independently_verified": False,
                        "files": comparisons})
print(json.dumps({"method": "HTTPS official version-matched APK payload byte comparison; no candidate bytes disclosed", "comparisons": results}, indent=2))
assert all(f["byte_equal"] for result in results for f in result["files"]), "STOP: unexplained binary difference"
