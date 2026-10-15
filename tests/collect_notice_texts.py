"""Collect selected original legal texts from checksum-verified source inputs.

Selection is finite and explicit. It is not a complete file-level license audit.
"""
import hashlib
import io
import json
import pathlib
import tarfile
import urllib.request

manifest = json.loads(pathlib.Path("docs/evidence/task0004-source-bundle-manifest.json").read_text())
selection = {
    "apk-tools": ["LICENSE"], "bash": ["COPYING"], "busybox": ["LICENSE"],
    "libmnl": ["COPYING"], "elfutils": ["COPYING", "COPYING-LGPLV3", "COPYING-GPLV2"],
    "iproute2": ["COPYING"], "iptables": ["COPYING"], "readline": ["COPYING"],
    "pax-utils": ["COPYING"], "libcap": ["License"],
    "c-ares": ["LICENSE.md"], "json-c": ["COPYING"],
    "openssl": ["LICENSE.txt"], "ncurses": ["COPYING"],
    "libyang": ["LICENSE"], "pcre2": ["LICENCE.md", "deps/sljit/LICENSE"],
    "tini": ["LICENSE"], "zlib": ["LICENSE"], "zstd": ["LICENSE"],
    "musl": ["COPYRIGHT"], "frr": ["COPYING"],
}
texts = []
for origin, wanted in selection.items():
    record = next(o for o in manifest["origins"] if o["origin"] == origin)
    found = set()
    for source in record["source_inputs"]:
        matches = [n for n in source.get("notice_members", []) if any(n["path"].split("/", 1)[-1] == p for p in wanted)]
        if not matches:
            continue
        with urllib.request.urlopen(source["url"], timeout=30) as response:
            data = response.read(64 * 1024 * 1024)
        assert hashlib.sha512(data).hexdigest() == source["expected_sha512"]
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            for notice in matches:
                body = archive.extractfile(notice["path"]).read()
                assert hashlib.sha256(body).hexdigest() == notice["sha256"]
                relative = notice["path"].split("/", 1)[-1]
                texts.append({"origin": origin, "version": record["version"],
                              "source_url": source["url"], "source_sha512": source["expected_sha512"],
                              "source_member": notice["path"], "sha256": notice["sha256"],
                              "destination": "licenses/third-party/" + origin + "-" + relative.replace("/", "_") + ".txt",
                              "text": "\n".join(line.rstrip() for line in body.decode("utf-8").splitlines()).rstrip() + "\n"})
                found.add(relative)
    assert set(wanted) == found, "STOP: selected legal text not found"
print(json.dumps(texts, indent=2))
