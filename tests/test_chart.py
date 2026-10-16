"""Helm is the validation engine: schema and semantic failures must reject render."""
import collections
import copy
import ipaddress
import json
import pathlib
import subprocess
import tempfile

import yaml

CHART = "charts/frr-route-reflector"
values = json.loads(pathlib.Path("examples/documentation-values.json").read_text())
docnets = [ipaddress.ip_network(x) for x in ["192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24"]]


def documentation_only(value):
    if isinstance(value, dict):
        for item in value.values(): documentation_only(item)
    elif isinstance(value, list):
        for item in value: documentation_only(item)
    elif isinstance(value, str) and value.count(".") == 3:
        try:
            ip = ipaddress.ip_address(value.split("/")[0])
        except ValueError:
            return
        if value == values["cluster"]["ospfArea"]: return
        assert any(ip in net for net in docnets), "non-documentation example IP"


documentation_only(values)


def helm(v, lint=False):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        json.dump(v, f)
        f.flush()
        args = ["helm", "lint", CHART] if lint else ["helm", "template", "rr", CHART]
        return subprocess.run(args + ["-f", f.name], capture_output=True, text=True)


assert helm(values, lint=True).returncode == 0
render = helm(values)
assert render.returncode == 0, render.stderr
assert render.stdout == helm(values).stdout, "nondeterministic render"
objects = [x for x in yaml.safe_load_all(render.stdout) if x]
assert collections.Counter(x["kind"] for x in objects) == {"Pod": 2, "ConfigMap": 2, "NetworkAttachmentDefinition": 8}
by_name = {o["metadata"]["name"]: o for o in objects if o["kind"] == "NetworkAttachmentDefinition"}
for rr in values["routers"]:
    name = "rr-" + rr["name"]
    pod = next(o for o in objects if o["kind"] == "Pod" and o["metadata"]["name"] == name)
    cm = next(o for o in objects if o["kind"] == "ConfigMap" and o["metadata"]["name"] == name)
    assert pod["spec"]["nodeSelector"] == rr["nodeSelector"]
    for flag in ["hostNetwork", "hostPID", "hostIPC", "automountServiceAccountToken"]:
        assert pod["spec"][flag] is False
    security = pod["spec"]["containers"][0]["securityContext"]
    assert security["allowPrivilegeEscalation"] is False and security["privileged"] is False
    assert security["capabilities"]["drop"] == ["ALL"]
    assert set(security["capabilities"]["add"]) == {"CHOWN", "SETUID", "SETGID", "NET_ADMIN", "NET_RAW", "NET_BIND_SERVICE", "SYS_ADMIN"}
    assert pod["spec"]["securityContext"]["seccompProfile"]["type"] == "RuntimeDefault"
    assert "sysctls" not in pod["spec"]["securityContext"]
    annotations = json.loads(pod["metadata"]["annotations"]["k8s.v1.cni.cncf.io/networks"])
    assert len(annotations) == 4
    for link in rr["links"]:
        attachment = next(a for a in annotations if a["interface"] == link["interface"])
        nad = json.loads(by_name[attachment["name"]]["spec"]["config"])
        assert nad["type"] == "vlan" and nad["master"] == rr["vlanMaster"]
        assert nad["vlanId"] == link["vlanId"]
        assert nad["ipam"] == {"type": "static", "addresses": [{"address": link["localAddress"]}]}
        assert "interface " + link["interface"] in cm["data"]["frr.conf"]
        assert f'{link["interface"]} {link["localAddress"]}' in cm["data"]["links"]
    config = cm["data"]["frr.conf"]
    assert config.count("route-reflector-client") == 4
    for forbidden in ["next-hop-self", "redistribute", "ipv6", "ospf6"]:
        assert forbidden not in config
    assert "bgp no-rib" in config and "max-metric router-lsa administrative" in config
    for client in values["clients"]:
        assert f'neighbor {client["loopback"].split("/")[0]} remote-as {values["cluster"]["bgpAsn"]}' in config
    for addr in [rr["routerId"], rr["loopback"].split("/")[0]]:
        assert ipaddress.ip_address(addr).is_global is False

cases = []


def bad(label, mutate):
    v = copy.deepcopy(values)
    mutate(v)
    cases.append((label, v))


bad("missing-profile", lambda v: v.pop("securityProfile"))
bad("bad-profile", lambda v: v.update(securityProfile="privileged"))
bad("too-few-RRs", lambda v: v["routers"].pop())
bad("too-many-RRs", lambda v: v["routers"].append(v["routers"][0]))
bad("too-few-clients", lambda v: v["clients"].pop())
bad("too-many-clients", lambda v: v["clients"].append(v["clients"][0]))
bad("duplicate-RR", lambda v: v["routers"][1].update(name="rr01"))
bad("invalid-RR-name", lambda v: v["routers"][0].update(name="rr-"))
bad("duplicate-client", lambda v: v["clients"][1].update(name="client1"))
bad("duplicate-routerid", lambda v: v["routers"][1].update(routerId="192.0.2.1"))
bad("duplicate-loopback", lambda v: v["routers"][1].update(loopback="192.0.2.1/32"))
bad("client-RR-collision", lambda v: v["clients"][0].update(loopback="192.0.2.1/32"))
bad("duplicate-worker", lambda v: v["routers"][1].update(nodeSelector=v["routers"][0]["nodeSelector"]))
bad("missing-link", lambda v: v["routers"][0]["links"].pop())
bad("duplicate-pair", lambda v: v["routers"][0]["links"][1].update(client="client1"))
bad("unknown-client", lambda v: v["routers"][0]["links"][1].update(client="unknown"))
bad("duplicate-vlan", lambda v: v["routers"][1]["links"][0].update(vlanId=1101))
bad("zero-vlan", lambda v: v["routers"][0]["links"][0].update(vlanId=0))
bad("high-vlan", lambda v: v["routers"][0]["links"][0].update(vlanId=4095))
bad("duplicate-if", lambda v: v["routers"][0]["links"][1].update(interface="net1"))
bad("primary-if", lambda v: v["routers"][0]["links"][0].update(interface="eth0"))
bad("wrong-mask", lambda v: v["routers"][0]["links"][0].update(localAddress="198.51.100.0/30"))
bad("invalid-octet", lambda v: v["routers"][0]["links"][0].update(localAddress="198.51.100.256/31"))
bad("overlapping-network", lambda v: v["routers"][1]["links"][0].update(localAddress="198.51.100.1/31"))
bad("loopback-network-collision", lambda v: v["routers"][0].update(loopback="198.51.100.0/32"))
bad("wrong-remote", lambda v: v["routers"][0]["links"][0].update(remoteAddress="198.51.100.2"))
bad("multicast", lambda v: v["routers"][0].update(routerId="224.0.0.1"))
bad("per-RR-clusterId", lambda v: v["routers"][0].update(clusterId="192.0.2.253"))
bad("forwarding-policy", lambda v: v.update(ipForward=True))
bad("extra-peer", lambda v: v["routers"][0].update(neighbors=["192.0.2.2"]))
bad("next-hop-policy", lambda v: v.update(nextHopSelf=True))
bad("arbitrary-FRR", lambda v: v.update(frrConfig="router bgp 1"))
bad("floating-image", lambda v: v.update(image="example.invalid/rr:latest"))
for label, v in cases:
    result = helm(v)
    assert result.returncode != 0, f"unsafe input accepted: {label}"
    print(f"negative {label}=PASS")
print(f"lint/schema/determinism/cardinality/mapping=PASS negatives={len(cases)}")

# Explicit bounded home mode; never infer co-location from a shortened peer list.
home = json.loads(pathlib.Path("examples/home-documentation-values.json").read_text())
documentation_only(home)
assert helm(home, lint=True).returncode == 0
result = helm(home)
assert result.returncode == 0, result.stderr
assert result.stdout == helm(home).stdout
home_objects = [o for o in yaml.safe_load_all(result.stdout) if o]
assert collections.Counter(o["kind"] for o in home_objects) == {"Pod": 2, "ConfigMap": 2, "NetworkAttachmentDefinition": 2}
for rr in home["routers"]:
    name = "rr-" + rr["name"]
    pod = next(o for o in home_objects if o["kind"] == "Pod" and o["metadata"]["name"] == name)
    cm = next(o for o in home_objects if o["kind"] == "ConfigMap" and o["metadata"]["name"] == name)
    assert pod["spec"]["nodeSelector"] == home["routers"][0]["nodeSelector"]
    attachments = json.loads(pod["metadata"]["annotations"]["k8s.v1.cni.cncf.io/networks"])
    assert len(attachments) == 1 and attachments[0]["interface"] == "net1"
    nad = next(o for o in home_objects if o["kind"] == "NetworkAttachmentDefinition" and o["metadata"]["name"] == attachments[0]["name"])
    config = json.loads(nad["spec"]["config"])
    link = rr["links"][0]
    assert config["master"] == rr["vlanMaster"] and config["vlanId"] == link["vlanId"]
    assert config["ipam"]["addresses"] == [{"address": link["localAddress"]}]
    assert cm["data"]["links"].splitlines() == [f'net1 {link["localAddress"]}']
    frr = cm["data"]["frr.conf"]
    assert frr.count("route-reflector-client") == 1 and "interface net1\n" in frr
    assert all(f"net{i}" not in frr for i in [2, 3, 4])
    assert "bgp no-rib" in frr and "max-metric router-lsa administrative" in frr
    assert not any(x in frr for x in ["next-hop-self", "redistribute", "ipv6", "ospf6"])

home_cases = []
def home_bad(label, mutate):
    v = copy.deepcopy(home)
    mutate(v)
    home_cases.append((label, v))

home_bad("implicit-home", lambda v: v.pop("topology"))
home_bad("home-four-mode", lambda v: v.update(topology="four-client"))
home_bad("unknown-mode", lambda v: v.update(topology="anything"))
home_bad("home-different-workers", lambda v: v["routers"][1].update(nodeSelector={"kubernetes.io/hostname": "worker-2.example.invalid"}))
home_bad("home-no-client", lambda v: v["clients"].clear())
home_bad("home-two-clients", lambda v: v["clients"].append(values["clients"][1]))
home_bad("home-four-clients", lambda v: v.update(clients=values["clients"]))
home_bad("home-phantom-interface", lambda v: v["routers"][0]["links"][0].update(interface="net2"))
home_bad("home-extra-link", lambda v: v["routers"][0]["links"].append(values["routers"][0]["links"][1]))
home_bad("home-unknown-client", lambda v: v["routers"][0]["links"][0].update(client="client2"))
home_bad("home-duplicate-vlan", lambda v: v["routers"][1]["links"][0].update(vlanId=1101))
home_bad("home-overlap", lambda v: v["routers"][1]["links"][0].update(localAddress="198.51.100.1/31"))
home_bad("home-duplicate-loopback", lambda v: v["routers"][1].update(loopback=v["routers"][0]["loopback"]))
for label, v in home_cases:
    assert helm(v).returncode != 0, f"unsafe home input accepted: {label}"
    print(f"negative {label}=PASS")
print(f"home lint/determinism/2+2+2/mapping=PASS negatives={len(home_cases)}")
