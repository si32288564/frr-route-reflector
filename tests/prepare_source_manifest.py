"""Finite source/notice preparation for frozen Task 0004 records.

Downloads HTTPS data for checksum checks; executes/installs/publishes nothing.
Does not claim complete corresponding source or legal compliance. No archives
are written into Git. Output is the reproducible proposed bundle manifest.
"""
import concurrent.futures
import hashlib
import io
import json
import pathlib
import re
import tarfile
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
recipes = json.loads((ROOT / "docs/evidence/task0004-source-recipe-probes.json").read_text())
images = json.loads((ROOT / "docs/evidence/task0004-image-inventory.json").read_text())["images"]


def fetch(url, limit=64 * 1024 * 1024):
    with urllib.request.urlopen(url, timeout=20) as response:
        data = response.read(limit + 1)
        assert len(data) <= limit, "download size bound"
        return data


def notice_inventory(data):
    result = []
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as archive:
            for member in archive:
                # Legal material only: do not export arbitrary source file bytes.
                if member.isfile() and member.size < 256 * 1024 and re.search(r"(?:^|/)(?:COPYING[^/]*|LICEN[CS]E[^/]*|NOTICE[^/]*|COPYRIGHT[^/]*)$", member.name, re.I):
                    body = archive.extractfile(member).read()
                    result.append({"path": member.name, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)})
    except tarfile.TarError:
        pass
    return result


def source_file(args):
    recipe, checksum, name = args
    assert not name.startswith("/") and ".." not in pathlib.PurePosixPath(name).parts
    urls = ["https://distfiles.alpinelinux.org/distfiles/v3.24/" + name,
            recipe["url"].rsplit("/", 1)[0] + "/" + name]
    result = {"name": name, "expected_sha512": checksum}
    errors = []
    for url in urls:
        try:
            data = fetch(url)
            actual = hashlib.sha512(data).hexdigest()
            if actual != checksum:
                errors.append({"url": url, "error": "SHA512 mismatch"})
                continue
            result.update(url=url, actual_sha512=actual, sha256=hashlib.sha256(data).hexdigest(),
                          bytes=len(data), status="VERIFIED", notice_members=notice_inventory(data))
            return result
        except (urllib.error.URLError, TimeoutError, AssertionError) as error:
            errors.append({"url": url, "error": str(error)})
    result.update(status="MISSING", attempts=errors)
    return result


def recipe_files(recipe):
    relative = recipe["url"].split(recipe["commit"] + "/", 1)[1].rsplit("/", 1)[0]
    url = "https://api.github.com/repos/alpinelinux/aports/contents/" + relative + "?ref=" + recipe["commit"]
    result, missing = [], []
    try:
        entries = json.loads(fetch(url, 2 * 1024 * 1024))
        assert isinstance(entries, list) and len(entries) <= 256
        for entry in entries:
            if entry["type"] != "file":
                missing.append({"path": entry["path"], "reason": "non-regular directory/symlink needs explicit inclusion review"})
                continue
            data = fetch(entry["download_url"], 2 * 1024 * 1024)
            git_sha = hashlib.sha1(("blob " + str(len(data)) + "\0").encode() + data).hexdigest()
            assert git_sha == entry["sha"], "recipe blob identity mismatch"
            result.append({"path": entry["path"], "url": entry["download_url"], "git_blob_sha1": git_sha,
                           "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    except (urllib.error.URLError, TimeoutError, AssertionError) as error:
        missing.append({"path": relative, "reason": str(error)})
    return result, missing


manifest = {"bundle_version": "v0.1.0-lab.1-sources.1", "publication": "NOT AUTHORIZED / NOT PUBLISHED",
            "images": [{"platform": i["architecture"], "local_manifest": i["docker_id"]} for i in images],
            "origins": []}
jobs = [(recipe, checksum, name) for recipe in recipes for checksum, name in recipe["sha512_entries"]]
assert len(jobs) <= 256
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
    checked = list(pool.map(source_file, jobs))
offset = 0
for recipe in recipes:
    count = len(recipe["sha512_entries"])
    inputs = checked[offset:offset + count]
    offset += count
    files, missing = recipe_files(recipe)
    packages = [p for p in images[0]["packages"] if p["origin"] == recipe["origin"]]
    expressions = sorted({p["declared_license"] for p in packages})
    # Conservative planning category, not a file-level license conclusion.
    required_source_review = any(re.search(r"GPL|MPL", expression) for expression in expressions)
    manifest["origins"].append({"origin": recipe["origin"], "version": recipe["version"],
                               "aports_commit": recipe["commit"],
                               "packages": [{"name": p["name"], "declared_license": p["declared_license"]} for p in packages],
                               "source_purpose": "copyleft source/notice review (OR choices pending)" if required_source_review else "notice extraction only; full source not mandated by this plan",
                               "recipe_files": files, "missing_recipe_material": missing, "source_inputs": inputs,
                               "copyright_and_license_review": "NOT VERIFIED; notice-member inventory is not complete attribution"})
manifest["verified_input_bytes"] = sum(s.get("bytes", 0) for s in checked)
manifest["verified_recipe_bytes"] = sum(f["bytes"] for o in manifest["origins"] for f in o["recipe_files"])
manifest["expected_bundle_size"] = "At least verified bytes plus missing material, selected notices and archive overhead; no complete bundle assembled"
manifest["unverified_inputs"] = sum(s["status"] != "VERIFIED" for s in checked)
manifest["missing_recipe_items"] = sum(len(o["missing_recipe_material"]) for o in manifest["origins"])
print(json.dumps(manifest, indent=2))
