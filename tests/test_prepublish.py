"""Offline consistency checks only; not legal, CVE or CycloneDX-schema clearance."""
import ast
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
ast.parse((ROOT / "tests/prepublish_inventory.py").read_text())
print("JSON/package/SBOM/recipe-version/source-sample/License/AST consistency=PASS")

helpers = runpy.run_path(str(ROOT / "tests/prepublish_inventory.py"))
counts = {key: 0 for key in helpers["PATTERNS"]}
history = subprocess.check_output(["git", "log", "-p", "origin/main", "--", "container", "charts", "tests", "README.md"], cwd=ROOT)
helpers["check"](history, counts)
files = ["LICENSE", "THIRD_PARTY_NOTICES.md", "README.md", "docs/publishing-preflight.md", "tests/prepublish_inventory.py", "tests/test_prepublish.py"]
for path in [ROOT / f for f in files] + list(EVIDENCE.glob("task0004-*")):
    if path.name != "task0004-validation.txt":
        helpers["check"](path.read_bytes(), counts)
print("Limited new-artifact/scoped-source-history heuristic counts=" + json.dumps(counts, sort_keys=True))
assert not any(counts.values())
print("Legal compliance/CVE scan/CycloneDX schema/native runtime=NOT RUN or BLOCKED")
