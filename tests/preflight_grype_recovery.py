#!/usr/bin/env python3
"""Task 0004 recovery: verify existing inputs; STOP before unsafe allocation.

Read-only Docker operations and data hashing only. Grype/target programs are
never executed here. The previous staging script remains immutable evidence.
"""
import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys

from scan_packaged_frr import BASE, IDENTITY, IMAGES, PINS, digest, inspect_image

LIMIT = 2 * 1024**3


def main():
    root = pathlib.Path(sys.argv[1]).resolve()
    assert root.parent == pathlib.Path("/tmp") and root.name.startswith("frr-task0004-grype.")
    previous = json.loads((root / "execution.json").read_text())
    report = {"started": dt.datetime.now(dt.timezone.utc).isoformat(), "commands": [],
              "checks": {}, "scanner_execution": "NOT RUN", "scans": {"amd64": "NOT RUN", "arm64": "NOT RUN"},
              "containers_created": [], "images_built": [], "contexts_created": []}
    failed = False
    try:
        for filename, expected in PINS.items():
            actual = digest(root / filename)
            assert actual == expected, "STOP: pinned scanner input mismatch"
            report["checks"][filename] = {"sha256": actual, "result": "PASS"}
        args = ["cosign", "verify-blob", str(root / "grype_0.120.1_checksums.txt"),
                "--bundle", str(root / "grype_0.120.1_checksums.txt.sigstore.json"),
                "--certificate-identity", IDENTITY,
                "--certificate-oidc-issuer", "https://token.actions.githubusercontent.com"]
        report["commands"].append([a.replace(str(root), "<task-temp>") for a in args])
        verified = subprocess.run(args, capture_output=True, timeout=60)
        report["checks"]["signature"] = {"exit": verified.returncode,
                                          "stdout": verified.stdout.decode(), "stderr": verified.stderr.decode(),
                                          "identity": IDENTITY}
        assert verified.returncode == 0, "STOP: signature verification failed"
        lines = (root / "grype_0.120.1_checksums.txt").read_text().splitlines()
        assert any(line.split() == [PINS["grype_0.120.1_linux_arm64.tar.gz"],
                                   "grype_0.120.1_linux_arm64.tar.gz"] for line in lines)
        binary = digest(root / "payload/grype")
        assert binary == previous["checks"]["grype_binary_sha256"], "STOP: binary mismatch"
        report["checks"]["grype_binary_sha256"] = binary
        meta = json.loads((root / "db-latest.json").read_text())
        assert meta["schemaVersion"] == "v6.1.10" and meta["status"] == "active"
        built = dt.datetime.fromisoformat(meta["built"].replace("Z", "+00:00"))
        age = (dt.datetime.now(dt.timezone.utc) - built).total_seconds()
        assert 0 <= age <= 432000, "STOP: DB is stale; approved same-publisher refresh needed"
        assert "sha256:" + digest(root / "db.tar.zst") == meta["checksum"]
        assert meta["checksum"] == previous["database"]["checksum"]
        report["database"] = dict(meta, age_seconds_at_check=age, max_age_seconds=432000,
                                  publisher="https://grype.anchore.io/databases/v6/latest.json",
                                  archive_url="https://grype.anchore.io/databases/v6/" + meta["path"],
                                  refresh="NOT NEEDED; reused approved snapshot")
        # Independent archive member-size inspection: no extraction or disk allocation.
        args = ["tar", "--zstd", "--numeric-owner", "-tvf", str(root / "db.tar.zst")]
        report["commands"].append([a.replace(str(root), "<task-temp>") for a in args])
        listing = subprocess.check_output(args, timeout=90).decode().splitlines()
        assert len(listing) == 1 and listing[0].split()[-1] == "vulnerability.db"
        member_size = int(listing[0].split()[2])
        path = root / "payload/db/6/vulnerability.db"
        assert path.stat().st_size == member_size
        actual = digest(path)
        assert actual == previous["database"]["sqlite_sha256"]
        report["database"].update(sqlite_sha256=actual, archive_member_bytes=member_size,
                                  existing_extracted_bytes=path.stat().st_size,
                                  existing_extracted_allocated_bytes=path.stat().st_blocks * 512)
        base = inspect_image(BASE)
        assert base["Architecture"] == "arm64" and base["Id"] == previous["sandbox_base"]["id"]
        report["sandbox_base"] = {"reference": BASE, "id": base["Id"], "architecture": base["Architecture"]}
        report["images"] = {}
        for arch, (image_hash, config_hash) in IMAGES.items():
            image = inspect_image("frr-task0003:" + arch)
            assert image["Id"] == "sha256:" + image_hash and image["Architecture"] == arch
            archive = root / "payload" / (arch + ".tar")
            actual = digest(archive)
            assert actual == previous["images"][arch]["archive_sha256"]
            import tarfile
            with tarfile.open(archive) as tar:
                manifest = json.load(tar.extractfile("manifest.json"))
                assert len(manifest) == 1
                config = tar.extractfile(manifest[0]["Config"]).read()
                assert hashlib.sha256(config).hexdigest() == config_hash
            report["images"][arch] = {"local_id": image["Id"], "config_sha256": config_hash,
                                      "archive_sha256": actual, "archive_bytes": archive.stat().st_size,
                                      "identity_check": "PASS"}
        report["capacity"] = {"memory_limit_bytes": LIMIT, "db_bytes": member_size,
                              "minimum_excess_bytes": max(0, member_size - LIMIT),
                              "counts_grype_indexes_and_other_memory": False}
        if member_size >= LIMIT:
            report["capacity"]["result"] = "FAIL"
            raise RuntimeError("STOP: DB alone exceeds 2 GiB; tmpfs import cannot fit approved memory limit")
        # Passing this necessary-size check alone would not establish hydration feasibility.
        report["capacity"]["result"] = "NECESSARY CHECK ONLY; runtime validation still required"
    except Exception as exc:
        failed = True
        report["stop"] = str(exc).replace(str(root), "<task-temp>")
    finally:
        report["ended"] = dt.datetime.now(dt.timezone.utc).isoformat()
        (root / "recovery-preflight.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"stopped": failed, "reason": report.get("stop"), "capacity": report.get("capacity")}))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
