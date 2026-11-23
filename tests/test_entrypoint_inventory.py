"""Unit-test the actual Bash inventory gate; no daemon/netns/runtime claims."""
import pathlib
import re
import subprocess

source = pathlib.Path("container/entrypoint.sh").read_text()
function = re.search(r"^validate_interface_inventory\(\) \{\n.*?^\}", source, re.M | re.S).group()
cases = [
    ("1", "eth0 lo net1 ", True),
    ("4", "eth0 lo net1 net2 net3 net4 ", True),
    ("0", "eth0 lo ", False),
    ("2", "eth0 lo net1 net2 ", False),
    ("3", "eth0 lo net1 net2 net3 ", False),
    ("5", "eth0 lo net1 net2 net3 net4 net5 ", False),
    ("1", "eth0 lo ", False),
    ("1", "eth0 lo net1 net2 ", False),
    ("1", "eth0 eth1 lo net1 ", False),
    ("1", "eth0 lo net2 ", False),
    ("4", "eth0 lo net1 net3 net4 ", False),
    ("4", "eth0 lo net1 net2 net3 net4 net5 ", False),
]
for count, inventory, accepted in cases:
    result = subprocess.run(["bash", "-c", function + '\nvalidate_interface_inventory "$1" "$2"', "test", count, inventory])
    assert (result.returncode == 0) == accepted, (count, inventory, result.returncode)
print(f"Actual entrypoint inventory gate unit cases=PASS count={len(cases)}")
