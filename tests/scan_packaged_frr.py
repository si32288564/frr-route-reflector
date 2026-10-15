#!/usr/bin/env python3
"""Task 0004 bounded scan; requires the specifically approved Workbox inputs.

No downloads, installs, registry access, target executables, or host mounts.
Inputs must already be acquired in a unique task temporary directory. A DB
installation failure is a STOP, not permission to invent import metadata,
disable validation, or change the scanner entrypoint/isolation.
"""
import datetime as dt
import hashlib
import json
import pathlib
import signal
import subprocess
import sys
import tarfile
import time
import uuid

PINS = {
    "grype_0.120.1_linux_arm64.tar.gz": "29f47391dc283aa79fcc38e65224cd61f64dec0ecfd0db7074128ebf8ff23514",
    "grype_0.120.1_checksums.txt": "c25b6095265b44fd9bbb9dbe76aca8daa394c5f0490793d2b52b16be4f5b71b1",
    "grype_0.120.1_checksums.txt.sigstore.json": "d6e9cd7e0e1c0384eb7f880640c61498388370d4bbf068ed3f84fc1941c511e8",
}
IMAGES = {
    "amd64": ("dbc288be32f2833223262801f287d4ba1be4594059a9a06001d31b963e2d428a", "7affa7841874770a1072a0e13ba497195434c8c2789b311471a53c8c3ab7a1be"),
    "arm64": ("dea86108c2812d9891674e0291af3b59872925e6c462e189a08acf0b3f61f096", "0bcae28f7ee60b01039bce6e402c89f3e2215859ac1e340ee5a16d8b57b57112"),
}
BASE = "alpine:3.24@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6"
IDENTITY = "https://github.com/anchore/grype/.github/workflows/release.yaml@refs/heads/main"


def run(args, **kwargs):
    return subprocess.run(args, check=True, timeout=kwargs.pop("timeout", 180), **kwargs)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def inspect_image(ref):
    return json.loads(run(["docker", "image", "inspect", ref], capture_output=True).stdout)[0]


def main():
    root = pathlib.Path(sys.argv[1]).resolve()
    assert root.parent == pathlib.Path("/tmp") and root.name.startswith("frr-task0004-grype.")
    report = {"started": utc(), "checks": {}, "scans": {}, "commands": []}
    owned = None
    failed = False

    def command(args, **kwargs):
        # Paths in published evidence are normalized, never host/user identifiers.
        report["commands"].append([str(a).replace(str(root), "<task-temp>") for a in args])
        return run(args, **kwargs)

    def cleanup():
        nonlocal owned
        if owned is None:
            return
        removed = subprocess.run(["docker", "rm", "-f", owned], capture_output=True, timeout=30)
        check = subprocess.run(["docker", "container", "inspect", owned], capture_output=True, timeout=30)
        report["scans"][arch]["cleanup"] = {
            "remove_exit": removed.returncode,
            "absence_inspect_exit": check.returncode,
            "absent": check.returncode == 1 and b"No such container" in check.stderr,
        }
        owned = None
        assert report["scans"][arch]["cleanup"]["absent"], "STOP: cleanup unconfirmed"

    def interrupted(signum, _frame):
        raise RuntimeError(f"interrupted by signal {signum}")

    signal.signal(signal.SIGTERM, interrupted)
    signal.signal(signal.SIGINT, interrupted)
    try:
        for filename, expected in PINS.items():
            actual = digest(root / filename)
            assert actual == expected, f"STOP: {filename} digest mismatch"
            report["checks"][filename] = actual
        command(["cosign", "verify-blob", str(root / "grype_0.120.1_checksums.txt"),
                 "--bundle", str(root / "grype_0.120.1_checksums.txt.sigstore.json"),
                 "--certificate-identity", IDENTITY,
                 "--certificate-oidc-issuer", "https://token.actions.githubusercontent.com"], timeout=60)
        report["checks"]["signature"] = "PASS"
        report["checks"]["certificate_identity"] = IDENTITY
        checksums = (root / "grype_0.120.1_checksums.txt").read_text().splitlines()
        assert any(line.split() == [PINS["grype_0.120.1_linux_arm64.tar.gz"],
                                   "grype_0.120.1_linux_arm64.tar.gz"] for line in checksums)
        metadata = json.loads((root / "db-latest.json").read_text())
        assert metadata["status"] == "active" and metadata["schemaVersion"] == "v6.1.10"
        built = dt.datetime.fromisoformat(metadata["built"].replace("Z", "+00:00"))
        age = (dt.datetime.now(dt.timezone.utc) - built).total_seconds()
        assert 0 <= age <= 432000, "STOP: DB age"
        db_hash = digest(root / "db.tar.zst")
        assert "sha256:" + db_hash == metadata["checksum"], "STOP: DB checksum"
        report["database"] = dict(metadata, archive_sha256=db_hash, age_seconds_at_check=age,
                                  url="https://grype.anchore.io/databases/v6/" + metadata["path"])
        payload = root / "payload"
        payload.mkdir()
        dbdir = payload / "db" / "6"
        dbdir.mkdir(parents=True)
        # Extract only the named regular DB file; never execute database inputs.
        listing = command(["tar", "--zstd", "-tf", str(root / "db.tar.zst")], capture_output=True).stdout
        assert listing == b"vulnerability.db\n", "STOP: unexpected DB members"
        command(["tar", "--zstd", "-xf", str(root / "db.tar.zst"), "-C", str(dbdir),
                 "--no-same-owner", "--no-same-permissions", "vulnerability.db"])
        (dbdir / "vulnerability.db").chmod(0o644)
        report["database"]["sqlite_sha256"] = digest(dbdir / "vulnerability.db")
        report["database"]["import_metadata"] = "absent in publisher archive; not fabricated"
        with tarfile.open(root / "grype_0.120.1_linux_arm64.tar.gz") as archive:
            member = archive.getmember("grype")
            assert member.isfile()
            with archive.extractfile(member) as source, (payload / "grype").open("xb") as dest:
                import shutil
                shutil.copyfileobj(source, dest)
        (payload / "grype").chmod(0o755)
        report["checks"]["grype_binary_sha256"] = digest(payload / "grype")
        base = inspect_image(BASE)
        assert base["Architecture"] == "arm64"
        report["sandbox_base"] = {"reference": BASE, "id": base["Id"], "architecture": base["Architecture"]}
        report["images"] = {}
        for arch, (image_hash, config_hash) in IMAGES.items():
            ref = "frr-task0003:" + arch
            image = inspect_image(ref)
            assert image["Id"] == "sha256:" + image_hash and image["Architecture"] == arch
            path = payload / (arch + ".tar")
            command(["docker", "image", "save", "-o", str(path), ref])
            with tarfile.open(path) as archive:
                manifest = json.load(archive.extractfile("manifest.json"))
                assert len(manifest) == 1
                config = archive.extractfile(manifest[0]["Config"]).read()
                assert hashlib.sha256(config).hexdigest() == config_hash
            assert inspect_image(ref)["Id"] == image["Id"]
            path.chmod(0o644)
            report["images"][arch] = {"local_id": image["Id"], "config_sha256": config_hash,
                                      "archive_sha256": digest(path), "archive_bytes": path.stat().st_size}
        for arch in IMAGES:
            name = "frr-task0004-grype-" + uuid.uuid4().hex
            collision = subprocess.run(["docker", "container", "inspect", name], capture_output=True, timeout=30)
            assert collision.returncode == 1 and b"No such container" in collision.stderr
            report["scans"][arch] = {"started": utc(), "unique_name": name, "collision_check": "PASS"}
            args = ["docker", "create", "--pull", "never", "--platform", "linux/arm64", "--name", name,
                    "--network", "none", "--user", "65534:65534", "--cap-drop", "ALL",
                    "--security-opt", "no-new-privileges:true", "--read-only", "--memory", "2g",
                    "--memory-swap", "2g", "--pids-limit", "64",
                    "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=536870912,mode=1777",
                    "--env", "HOME=/tmp", "--env", "GRYPE_DB_CACHE_DIR=/work/db",
                    "--env", "GRYPE_DB_AUTO_UPDATE=false", "--env", "GRYPE_CHECK_FOR_APP_UPDATE=false",
                    "--env", "GRYPE_DB_VALIDATE_BY_HASH_ON_START=true", "--env", "GRYPE_DB_VALIDATE_AGE=true",
                    "--env", "GRYPE_DB_MAX_ALLOWED_BUILT_AGE=120h", "--entrypoint", "/work/grype",
                    BASE, "docker-archive:/work/" + arch + ".tar", "-o", "json", "--fail-on", "high"]
            # Claim exact task name before creation so failures cannot strand it.
            owned = name
            command(args, capture_output=True, timeout=30)
            command(["docker", "cp", str(payload) + "/.", name + ":/work"], timeout=180)
            inspected = json.loads(command(["docker", "container", "inspect", name], capture_output=True).stdout)[0]
            hc = inspected["HostConfig"]
            report["scans"][arch]["isolation"] = {key: hc[key] for key in [
                "NetworkMode", "PidMode", "IpcMode", "Privileged", "ReadonlyRootfs", "CapAdd", "CapDrop",
                "SecurityOpt", "Memory", "MemorySwap", "PidsLimit", "Tmpfs", "Binds", "Devices"]}
            report["scans"][arch]["user"] = inspected["Config"]["User"]
            report["scans"][arch]["environment"] = inspected["Config"]["Env"]
            report["scans"][arch]["mounts"] = inspected["Mounts"]
            assert not hc["Privileged"] and hc["ReadonlyRootfs"] and hc["NetworkMode"] == "none"
            assert not hc["CapAdd"] and hc["CapDrop"] == ["ALL"] and not hc["Binds"] and not hc["Devices"]
            assert hc["Memory"] == 2147483648 and hc["PidsLimit"] == 64
            start = time.monotonic()
            with (root / (arch + "-scan.json")).open("xb") as out, (root / (arch + "-scan.stderr")).open("xb") as err:
                proc = subprocess.run(["timeout", "--signal=TERM", "--kill-after=5", "595",
                                       "docker", "start", "-a", name], stdout=out, stderr=err, timeout=605)
            report["scans"][arch].update(external_exit=proc.returncode, elapsed_seconds=time.monotonic() - start,
                                         ended=utc(), external_timeout_seconds=600)
            state = json.loads(command(["docker", "container", "inspect", name], capture_output=True).stdout)[0]["State"]
            report["scans"][arch]["state"] = {k: state[k] for k in ["Status", "Running", "OOMKilled", "ExitCode", "Error", "StartedAt", "FinishedAt"]}
            cleanup()
            if proc.returncode not in (0, 2):
                raise RuntimeError("STOP: scanner operational failure; remaining architecture NOT RUN")
            scan = json.loads((root / (arch + "-scan.json")).read_text())
            assert scan["descriptor"]["version"] == "0.120.1" and "matches" in scan
            report["scans"][arch]["result"] = "PASS execution; findings require separate disposition"
    except Exception as exc:
        failed = True
        report["stop"] = str(exc).replace(str(root), "<task-temp>")
    finally:
        try:
            cleanup()
        finally:
            report["ended"] = utc()
            (root / "execution.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"stopped": failed, "scanned": list(report["scans"]), "stop": report.get("stop")}))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
