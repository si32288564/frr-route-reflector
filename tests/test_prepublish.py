"""Offline consistency checks only; not legal, CVE or CycloneDX-schema clearance."""
import ast
import hashlib
import json
import pathlib
import runpy
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "docs/evidence"


def read(name):
    return json.loads((EVIDENCE / name).read_text())


inventory = read("task0004-image-inventory.json")
sbom = read("task0004-apk-sbom.cdx.json")
recipes = read("task0004-source-recipe-probes.json")
samples = read("task0004-source-sample-checks.json")
assert {i["architecture"] for i in inventory["images"]} == {"amd64", "arm64"}
assert all(len(i["packages"]) == 35 for i in inventory["images"])
assert len(sbom["components"]) == 70
assert len({c["bom-ref"] for c in sbom["components"]}) == 70
assert len(recipes) == 25 and all(r["http"] == 200 for r in recipes)
left, right = [i["packages"] for i in inventory["images"]]
assert all(all(a[k] == b[k] for k in ("name", "version", "declared_license", "origin", "upstream", "aports_commit")) for a, b in zip(left, right))
for image in inventory["images"]:
    for package in image["packages"]:
        recipe = next(r for r in recipes if r["origin"] == package["origin"])
        assert package["version"] == recipe["pkgver"][0] + "-r" + recipe["pkgrel"][0]
        assert package["aports_commit"] == recipe["commit"]
        component = next(c for c in sbom["components"] if c["bom-ref"] == image["architecture"] + ":" + package["name"] + "@" + package["version"])
        assert component["licenses"][0]["expression"] == package["declared_license"]
assert all(s["checksum_match"] and s["expected"] == s["actual_sha512"] for s in samples["source_checks"])
assert all(c["candidates"] == 2 for c in samples["candidate_comparison"])
license_text = (ROOT / "LICENSE").read_text()
assert license_text.startswith("MIT License\n")
assert "Copyright (c) 2026 si32288564" in license_text
assert 'THE SOFTWARE IS PROVIDED "AS IS"' in license_text
bundle = read("task0004-source-bundle-manifest.json")
assert len(bundle["origins"]) == 25
assert bundle["unverified_inputs"] == 0 and bundle["missing_recipe_items"] == 0
assert sum(len(o["source_inputs"]) for o in bundle["origins"]) == 173
assert sum(len(o["recipe_files"]) for o in bundle["origins"]) == 180
assert all(s["status"] == "VERIFIED" and s["expected_sha512"] == s["actual_sha512"] for o in bundle["origins"] for s in o["source_inputs"])
assert bundle["verified_input_bytes"] == sum(s["bytes"] for o in bundle["origins"] for s in o["source_inputs"])
notices = read("task0004-notice-texts.json")
assert len(notices) == 24
for notice in notices:
    assert hashlib.sha256((ROOT / notice["destination"]).read_bytes()).hexdigest() == notice["stored_sha256"]
comparison = read("task0004-official-binary-comparison.json")
assert len(comparison["comparisons"]) == 4
assert all(f["byte_equal"] and f["image_sha256"] == f["official_sha256"] for p in comparison["comparisons"] for f in p["files"])
assert sum(sum(f["candidate_counts"].values()) for p in comparison["comparisons"] for f in p["files"]) == 22
assert read("task0004-cyclonedx-schema.json")["result"] == "PASS"
assert len(read("task0004-elf-linkage.json")["records"]) == 20
scan = read("task0004-grype-execution.json")
assert scan["checks"]["signature"] == "PASS"
assert scan["database"]["checksum"] == "sha256:" + scan["database"]["archive_sha256"]
assert 0 <= scan["database"]["age_seconds_at_check"] <= 432000
assert scan["database"]["schemaVersion"] == "v6.1.10"
for image in inventory["images"]:
    arch = image["architecture"]
    assert scan["images"][arch]["config_sha256"] == image["config_sha256"]
assert list(scan["scans"]) == ["amd64"]  # Staging attempt only, NOT a CVE scan.
assert scan["scans"]["amd64"]["cleanup"] == {
    "remove_exit": 0, "absence_inspect_exit": 1, "absent": True}
assert "'docker', 'cp'" in scan["stop"]
assert not any(command[:2] == ["docker", "start"] for command in scan["commands"])
assert "matches" not in scan and "external_exit" not in scan["scans"]["amd64"]
recovery = read("task0004-grype-recovery-preflight.json")
assert recovery["checks"]["signature"]["exit"] == 0
assert recovery["database"]["checksum"] == scan["database"]["checksum"]
assert recovery["database"]["sqlite_sha256"] == scan["database"]["sqlite_sha256"]
assert 0 <= recovery["database"]["age_seconds_at_check"] <= 432000
assert recovery["images"] == {arch: dict(image, identity_check="PASS") for arch, image in scan["images"].items()}
assert recovery["capacity"]["db_bytes"] == 2463731712
assert recovery["capacity"]["memory_limit_bytes"] == 2147483648
assert recovery["capacity"]["minimum_excess_bytes"] == 316248064
assert recovery["capacity"]["result"] == "FAIL"
assert all(not recovery[key] for key in ("containers_created", "images_built", "contexts_created"))
assert recovery["scans"] == {"amd64": "NOT RUN", "arm64": "NOT RUN"}
assert read("task0004-grype-recovery-schema.json")["result"] == "PASS"
instructions = [line.split()[0] for line in (ROOT / "tests/grype-sandbox/Dockerfile").read_text().splitlines()
                if line.strip() and not line.startswith("#")]
assert set(instructions) <= {"FROM", "COPY", "ENV", "USER", "ENTRYPOINT"}
assert instructions.count("FROM") == 1 and instructions.count("COPY") == 3
subprocess.run(["sh", "-n", str(ROOT / "tests/grype-sandbox/init.sh")], check=True)
for name in ["prepublish_inventory", "classify_packaged_findings", "prepare_source_manifest", "collect_notice_texts", "inspect_packaged_linkage", "validate_cyclonedx_schema", "scan_packaged_frr", "preflight_grype_recovery"]:
    ast.parse((ROOT / ("tests/" + name + ".py")).read_text())
print("JSON/package/SBOM/recipe-version/source-sample/License/AST consistency=PASS")
print("173-input/180-recipe/24-notice/22-candidate/formal-schema-record consistency=PASS")
print("Grype/DB identity and staging-STOP/cleanup record consistency=PASS; CVEs=NOT RUN")
print("Recovery frozen-input/capacity-STOP/schema-record/COPY-only/shell-syntax consistency=PASS; build/scan=NOT RUN")

helpers = runpy.run_path(str(ROOT / "tests/prepublish_inventory.py"))
counts = {key: 0 for key in helpers["PATTERNS"]}
history = subprocess.check_output(["git", "log", "-p", "origin/main", "--", "container", "charts", "tests", "README.md"], cwd=ROOT)
helpers["check"](history, counts)
files = ["LICENSE", "THIRD_PARTY_NOTICES.md", "README.md", "docs/publishing-preflight.md", "docs/source-bundle-plan.md", "docs/scanner-approval-proposal.md", "docs/task0004-grype-stop.md", "docs/task0004-grype-recovery.md", "tests/preflight_grype_recovery.py", "tests/grype-sandbox/Dockerfile", "tests/grype-sandbox/init.sh", "tests/scan_packaged_frr.py", "tests/prepublish_inventory.py", "tests/test_prepublish.py", "tests/classify_packaged_findings.py", "tests/prepare_source_manifest.py", "tests/collect_notice_texts.py", "tests/inspect_packaged_linkage.py", "tests/validate_cyclonedx_schema.py"]
for path in [ROOT / f for f in files] + list(EVIDENCE.glob("task0004-*")) + list((ROOT / "licenses/third-party").glob("*.txt")):
    if path.name not in {"task0004-validation.txt", "task0004-continuation-validation.txt"}:
        helpers["check"](path.read_bytes(), counts)
print("Limited new-artifact/scoped-source-history heuristic counts=" + json.dumps(counts, sort_keys=True))
assert not any(counts.values())
print("Formal CycloneDX schema=PASS recorded; legal compliance/CVE scan/native runtime=NOT RUN or BLOCKED")
