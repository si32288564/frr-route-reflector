"""Validate with already installed jsonschema; fetch schema DATA, not tools."""
import hashlib
import importlib.metadata
import json
import pathlib
import urllib.error
import urllib.request

import jsonschema

schemas = {}


def fetch(url):
    assert url.startswith(("https://cyclonedx.org/schema/", "http://cyclonedx.org/schema/")), "unexpected schema origin"
    mirror = "https://raw.githubusercontent.com/CycloneDX/specification/1.6/schema/" + url.rsplit("/", 1)[-1]
    actual_url = url.replace("http://", "https://")
    try:
        response = urllib.request.urlopen(actual_url, timeout=20)
    except urllib.error.HTTPError as error:
        if error.code != 403:
            raise
        actual_url = mirror
        response = urllib.request.urlopen(actual_url, timeout=20)
    with response:
        body = response.read(2 * 1024 * 1024 + 1)
    assert len(body) <= 2 * 1024 * 1024
    schemas[url] = {"source_url": actual_url, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
    return json.loads(body)


url = "https://cyclonedx.org/schema/bom-1.6.schema.json"
schema = fetch(url)
validator = jsonschema.validators.validator_for(schema)
validator.check_schema(schema)
resolver = jsonschema.RefResolver(base_uri=url, referrer=schema, handlers={"https": fetch, "http": fetch})
bom = json.loads(pathlib.Path("docs/evidence/task0004-apk-sbom.cdx.json").read_text())
errors = sorted(validator(schema, resolver=resolver).iter_errors(bom), key=lambda e: str(e.path))
print(json.dumps({"tool": "jsonschema", "version": importlib.metadata.version("jsonschema"),
                  "schema": url, "retrieved_schemas": schemas,
                  "instance": "task0004-apk-sbom.cdx.json", "result": "PASS" if not errors else "FAIL",
                  "errors": [str(e.message) for e in errors]}, indent=2))
assert not errors
