"""Read-only, bounded offline APK inventory and heuristic disclosure check.

Uses existing Docker save/inspect/history only: no run, build, login or push.
Not a vulnerability scanner, license audit or proof that an image is secret-free.
JSON output contains package metadata and finding counts, never matching bytes.
"""
import hashlib
import io
import json
import re
import subprocess
import sys
import tarfile

PATTERNS = {
    "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
    "github_token": rb"gh[pousr]_[A-Za-z0-9]{30,}",
    "docker_pat": rb"dckr_pat_[A-Za-z0-9_-]{20,}",
    "internal_domain": rb"\b[A-Za-z0-9.-]+\.(?:mgmt|core|int)\.[A-Za-z0-9.-]+\b|\b[A-Za-z0-9.-]+\.(?:internal|local)\b",
    "credential_assignment": rb"(?i)(?:password|token|secret)\s*=\s*['\"]?[A-Za-z0-9_/-]{16,}",
}


def command(*args):
    return subprocess.run(args, check=True, capture_output=True, timeout=90).stdout


def check(data, counts):
    found = []
    for label, pattern in PATTERNS.items():
        hits = len(re.findall(pattern, data))
        counts[label] += hits
        if hits:
            found.append(label)
    return found


def inventory(image):
    inspect = json.loads(command("docker", "image", "inspect", image))[0]
    history = command("docker", "history", "--no-trunc", "--format", "{{json .}}", image)
    counts = {key: 0 for key in PATTERNS}
    counts["credential_file_path"] = 0
    check(json.dumps(inspect["Config"]).encode(), counts)
    check(history, counts)
    archive_bytes = command("docker", "image", "save", image)
    installed = None
    notices = set()
    locations = []
    members_scanned = 0
    with tarfile.open(fileobj=io.BytesIO(archive_bytes)) as archive:
        manifest = json.load(archive.extractfile("manifest.json"))
        assert len(manifest) == 1, "one image per archive required"
        entry = manifest[0]
        config = archive.extractfile(entry["Config"]).read()
        for layer_name in entry["Layers"]:
            with tarfile.open(fileobj=archive.extractfile(layer_name), mode="r|*") as layer:
                for member in layer:
                    path = member.name.removeprefix("./").lstrip("/")
                    if path.endswith(".docker/config.json") or path.endswith(".ssh/id_rsa") or path.endswith(".ssh/id_ed25519") or path == ".env":
                        counts["credential_file_path"] += 1
                    if not member.isfile():
                        continue
                    assert member.size <= 128 * 1024 * 1024, "member bound exceeded"
                    data = layer.extractfile(member).read()
                    members_scanned += 1
                    found = check(data, counts)
                    if found:
                        locations.append({"path": path, "categories": found,
                                          "elf": data.startswith(b"\x7fELF")})
                    if path == "lib/apk/db/installed":
                        installed = data.decode()
                    if path == "lib/apk/db/.wh.installed":
                        installed = None
                    if re.search(r"(?:^|/)(?:licenses?|copying|copyright|notice)(?:[./_-]|$)", path, re.I):
                        notices.add(path)
    assert installed is not None, "installed APK database missing"
    packages = []
    keys = {"P": "name", "V": "version", "A": "architecture", "L": "declared_license", "U": "upstream", "o": "origin", "c": "aports_commit", "C": "apk_checksum"}
    for record in installed.strip().split("\n\n"):
        fields = {}
        for line in record.splitlines():
            key, separator, value = line.partition(":")
            if separator and key in keys:
                fields[keys[key]] = value
        if fields.get("name"):
            packages.append(fields)
    assert len(packages) == 35
    return {
        "image": image, "docker_id": inspect["Id"],
        "architecture": inspect["Architecture"], "os": inspect["Os"],
        "config_sha256": hashlib.sha256(config).hexdigest(),
        "layer_count": len(entry["Layers"]), "regular_layer_entries_scanned": members_scanned,
        "disclosure_heuristic_counts": counts, "disclosure_locations": locations,
        "notice_paths_observed": sorted(notices),
        "packages": sorted(packages, key=lambda p: p["name"]),
    }


if __name__ == "__main__":
    assert len(sys.argv) == 3, "supply exactly two existing local images"
    print(json.dumps({"format": "task0004-apk-inventory-v1", "scanner": "heuristic only; no CVE database", "images": [inventory(image) for image in sys.argv[1:]]}, indent=2))
