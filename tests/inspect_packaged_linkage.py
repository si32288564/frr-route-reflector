"""Read only ELF NEEDED entries with existing readelf; execute no image code."""
import io
import json
import os
import re
import subprocess
import tarfile

results = []
for image in ["frr-task0003:amd64", "frr-task0003:arm64"]:
    data = subprocess.run(["docker", "save", image], check=True, capture_output=True, timeout=90).stdout
    files = {}
    with tarfile.open(fileobj=io.BytesIO(data)) as archive:
        manifest = json.load(archive.extractfile("manifest.json"))[0]
        for layer_name in manifest["Layers"]:
            with tarfile.open(fileobj=archive.extractfile(layer_name), mode="r|*") as layer:
                for member in layer:
                    path = member.name.removeprefix("./").lstrip("/")
                    wanted = path in {"sbin/apk", "usr/bin/vtysh", "usr/lib/frr/bgpd", "usr/lib/frr/zebra", "usr/lib/frr/ospfd", "usr/lib/frr/mgmtd"} or path.startswith(("usr/lib/libapk.so.", "usr/lib/frr/libfrr.so.", "usr/lib/libelf.so.", "usr/lib/libelf-", "usr/lib/libreadline.so."))
                    if wanted and member.isfile():
                        files[path] = layer.extractfile(member).read()
    for path, body in sorted(files.items()):
        fd = os.memfd_create("read-only-elf-inspection")
        try:
            os.write(fd, body)
            result = subprocess.run(["readelf", "-d", "/proc/self/fd/" + str(fd)], pass_fds=(fd,), check=True, capture_output=True, text=True, timeout=10)
            needed = re.findall(r"\(NEEDED\).*?\[(.*?)\]", result.stdout)
            results.append({"image": image, "path": path, "needed": needed})
        finally:
            os.close(fd)
print(json.dumps({"method": "existing readelf dynamic-section inspection, no executable launch", "records": results}, indent=2))
