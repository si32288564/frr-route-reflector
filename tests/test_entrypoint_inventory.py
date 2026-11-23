"""Unit-test the actual Bash inventory gate; no daemon/netns/runtime claims."""
import pathlib
import re
import subprocess

source = pathlib.Path("container/entrypoint.sh").read_text()
function = "\n".join(re.search(r"^" + name + r"\(\) \{\n.*?^\}", source, re.M | re.S).group()
                     for name in ["validate_inactive_tunl0", "validate_interface_inventory"])
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

# Only command readbacks are mocked; execute the production Bash functions.
mock = r'''
ip() {
  case "$*" in
    '-o link show dev tunl0') printf '%s\n' "$TUN_LINK"; return "$LINK_RC" ;;
    '-4 -o addr show dev tunl0') printf '%s' "$TUN_V4"; return "$V4_RC" ;;
    '-6 -o addr show dev tunl0') printf '%s' "$TUN_V6"; return "$V6_RC" ;;
    *) return 99 ;;
  esac
}
'''
down = "4: tunl0@NONE: <NOARP> mtu 1480 qdisc noop state DOWN mode DEFAULT group default"
base = {"TUN_LINK": down, "TUN_V4": "", "TUN_V6": "", "LINK_RC": "0", "V4_RC": "0", "V6_RC": "0"}
tunnel_cases = [
    ("inactive-core", "1", "eth0 lo net1 tunl0 ", {}, True),
    ("inactive-default", "4", "eth0 lo net1 net2 net3 net4 tunl0 ", {}, True),
    ("admin-up", "1", "eth0 lo net1 tunl0 ", {"TUN_LINK": down.replace("<NOARP>", "<NOARP,UP>")}, False),
    ("oper-up", "1", "eth0 lo net1 tunl0 ", {"TUN_LINK": down.replace("state DOWN", "state UP")}, False),
    ("unknown-state", "1", "eth0 lo net1 tunl0 ", {"TUN_LINK": down.replace("state DOWN", "state UNKNOWN")}, False),
    ("ipv4", "1", "eth0 lo net1 tunl0 ", {"TUN_V4": "4: tunl0 inet 192.0.2.1/32"}, False),
    ("ipv6", "1", "eth0 lo net1 tunl0 ", {"TUN_V6": "4: tunl0 inet6 fe80::1/64 scope link"}, False),
    ("link-read-failed", "1", "eth0 lo net1 tunl0 ", {"LINK_RC": "1"}, False),
    ("v4-read-failed", "1", "eth0 lo net1 tunl0 ", {"V4_RC": "1"}, False),
    ("v6-read-failed", "1", "eth0 lo net1 tunl0 ", {"V6_RC": "1"}, False),
    ("malformed-link", "1", "eth0 lo net1 tunl0 ", {"TUN_LINK": "state DOWN"}, False),
    ("missing-net1", "1", "eth0 lo tunl0 ", {}, False),
    ("extra-net2", "1", "eth0 lo net1 net2 tunl0 ", {}, False),
    ("extra-eth1", "1", "eth0 eth1 lo net1 tunl0 ", {}, False),
    ("other-tunnel", "1", "eth0 lo net1 tunl1 ", {}, False),
    ("two-tunnels", "1", "eth0 lo net1 tunl0 tunl1 ", {}, False),
    ("default-missing-net4", "4", "eth0 lo net1 net2 net3 tunl0 ", {}, False),
]
import os
for label, count, inventory, changed, accepted in tunnel_cases:
    result = subprocess.run(["bash", "-c", mock + function + '\nvalidate_interface_inventory "$1" "$2"', "test", count, inventory],
                            env={**os.environ, **base, **changed})
    assert (result.returncode == 0) == accepted, (label, result.returncode)
print(f"Inactive tunl0 actual-function cases=PASS count={len(tunnel_cases)}")
