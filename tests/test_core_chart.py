"""Core OSPF links and iBGP peers are independent; import runs old regressions."""
import collections
import copy
import json
import pathlib

import yaml
from test_chart import helm, documentation_only

core = json.loads(pathlib.Path("examples/core-documentation-values.json").read_text())
documentation_only(core)


def check(v):
    assert helm(v, lint=True).returncode == 0
    result = helm(v)
    assert result.returncode == 0, result.stderr
    assert result.stdout == helm(v).stdout
    objects = [o for o in yaml.safe_load_all(result.stdout) if o]
    assert collections.Counter(o["kind"] for o in objects) == {"Pod": 2, "ConfigMap": 2, "NetworkAttachmentDefinition": 2}
    for rr in v["routers"]:
        name = "rr-" + rr["name"]
        pod = next(o for o in objects if o["kind"] == "Pod" and o["metadata"]["name"] == name)
        cm = next(o for o in objects if o["kind"] == "ConfigMap" and o["metadata"]["name"] == name)
        link = rr["links"][0]
        attachments = json.loads(pod["metadata"]["annotations"]["k8s.v1.cni.cncf.io/networks"])
        assert len(attachments) == 1 and attachments[0]["interface"] == "net1"
        nad = next(o for o in objects if o["kind"] == "NetworkAttachmentDefinition" and o["metadata"]["name"] == attachments[0]["name"])
        network = json.loads(nad["spec"]["config"])
        assert network == {"cniVersion": "0.3.1", "name": name + "-net1", "type": "vlan", "master": rr["vlanMaster"], "vlanId": link["vlanId"], "ipam": {"type": "static", "addresses": [{"address": link["localAddress"]}]}}
        assert cm["data"]["links"].splitlines() == [f'net1 {link["localAddress"]}']
        config = cm["data"]["frr.conf"]
        assert [s for s in config.splitlines() if s.startswith("interface ")] == ["interface lo", "interface net1"]
        assert config.count("ip ospf network point-to-point") == 1
        assert "ip ospf passive" in config
        assert f'bgp cluster-id {rr["loopback"].split("/")[0]}' in config
        assert "bgp no-rib" in config and "max-metric router-lsa administrative" in config
        assert not any(x in config for x in ["next-hop-self", "redistribute", "ipv6", "ospf6"])
        lines = [s.strip() for s in config.splitlines()]
        assert sum(s.startswith("neighbor ") and " remote-as " in s for s in lines) == len(rr["neighbors"])
        for peer in rr["neighbors"]:
            address = peer["address"]
            assert f'neighbor {address} remote-as {v["cluster"]["bgpAsn"]}' in lines
            assert f'neighbor {address} update-source {rr["loopback"].split("/")[0]}' in lines
            assert f"neighbor {address} activate" in lines
            assert (f"neighbor {address} route-reflector-client" in lines) == peer["routeReflectorClient"]
        assert config.count("route-reflector-client") == sum(p["routeReflectorClient"] for p in rr["neighbors"])
        assert pod["spec"]["nodeSelector"] == rr["nodeSelector"]
        for flag in ["hostNetwork", "hostPID", "hostIPC", "automountServiceAccountToken"]:
            assert pod["spec"][flag] is False
        security = pod["spec"]["containers"][0]["securityContext"]
        assert not security["privileged"] and not security["allowPrivilegeEscalation"]
        assert security["capabilities"]["drop"] == ["ALL"]
        assert set(security["capabilities"]["add"]) == {"CHOWN", "SETUID", "SETGID", "NET_ADMIN", "NET_RAW", "NET_BIND_SERVICE", "SYS_ADMIN"}
        assert pod["spec"]["securityContext"]["seccompProfile"]["type"] == "RuntimeDefault"
        assert "sysctls" not in pod["spec"]["securityContext"]
    return objects


original = check(core)
for count in [1, 2, 10]:
    v = copy.deepcopy(core)
    for rr in v["routers"]:
        rr["neighbors"] = [{"address": f"192.0.2.{20+i}", "routeReflectorClient": True} for i in range(count)]
    check(v)
home = copy.deepcopy(core)
home["placement"] = "single-worker"
home["routers"][1]["nodeSelector"] = copy.deepcopy(home["routers"][0]["nodeSelector"])
check(home)
changed = copy.deepcopy(core)
changed["routers"][0]["neighbors"].append({"address": "192.0.2.30", "routeReflectorClient": True})
after = check(changed)
assert [o for o in original if o["kind"] == "NetworkAttachmentDefinition"] == [o for o in after if o["kind"] == "NetworkAttachmentDefinition"]
assert next(o for o in original if o["kind"] == "ConfigMap" and o["metadata"]["name"] == "rr-rr02") == next(o for o in after if o["kind"] == "ConfigMap" and o["metadata"]["name"] == "rr-rr02")

cases = []
def bad(label, mutate):
    v = copy.deepcopy(core)
    mutate(v)
    cases.append((label, v))

bad("no-opt-in", lambda v: v.pop("topology"))
bad("unknown-topology", lambda v: v.update(topology="unknown"))
bad("mixed-global-clients", lambda v: v["clients"].append({"name": "client1", "loopback": "192.0.2.11/32"}))
bad("missing-peers", lambda v: v["routers"][0].pop("neighbors"))
bad("empty-peers", lambda v: v["routers"][0].update(neighbors=[]))
bad("duplicate-peer", lambda v: v["routers"][0]["neighbors"].append(v["routers"][0]["neighbors"][0]))
bad("self-peer", lambda v: v["routers"][0]["neighbors"][0].update(address="192.0.2.1"))
bad("RR-is-client", lambda v: v["routers"][0]["neighbors"][-1].update(routeReflectorClient=True))
bad("missing-role", lambda v: v["routers"][0]["neighbors"][0].pop("routeReflectorClient"))
bad("string-role", lambda v: v["routers"][0]["neighbors"][0].update(routeReflectorClient="false"))
bad("no-RR-client", lambda v: v["routers"][0].update(neighbors=[{"address": "192.0.2.2", "routeReflectorClient": False}]))
bad("peer-ASN-override", lambda v: v["routers"][0]["neighbors"][0].update(remoteAs=64513))
bad("peer-raw-FRR", lambda v: v["routers"][0]["neighbors"][0].update(config="next-hop-self"))
bad("invalid-peer", lambda v: v["routers"][0]["neighbors"][0].update(address="192.0.2.256"))
bad("multicast-peer", lambda v: v["routers"][0]["neighbors"][0].update(address="224.0.0.1"))
bad("masked-peer", lambda v: v["routers"][0]["neighbors"][0].update(address="192.0.2.11/32"))
bad("peer-link-overlap", lambda v: v["routers"][0]["neighbors"][0].update(address="198.51.100.1"))
bad("missing-link", lambda v: v["routers"][0].update(links=[]))
bad("extra-link", lambda v: v["routers"][0]["links"].append(copy.deepcopy(v["routers"][0]["links"][0])))
bad("wrong-interface", lambda v: v["routers"][0]["links"][0].update(interface="net2"))
bad("mixed-link-client", lambda v: v["routers"][0]["links"][0].update(client="client1"))
bad("missing-core-address", lambda v: v["routers"][0]["links"][0].pop("remoteAddress"))
bad("wrong-core-address", lambda v: v["routers"][0]["links"][0].update(remoteAddress="198.51.100.2"))
bad("same-core-address", lambda v: v["routers"][0]["links"][0].update(remoteAddress="198.51.100.0"))
bad("duplicate-VLAN", lambda v: v["routers"][1]["links"][0].update(vlanId=1101))
bad("duplicate-subnet", lambda v: v["routers"][1]["links"][0].update(localAddress="198.51.100.0/31", remoteAddress="198.51.100.1"))
bad("duplicate-loopback", lambda v: v["routers"][1].update(loopback="192.0.2.1/32"))
bad("shared-ClusterID", lambda v: v["cluster"].update(clusterId="192.0.2.254"))
bad("implicit-colocation", lambda v: v["routers"][1].update(nodeSelector=v["routers"][0]["nodeSelector"]))
bad("single-worker-mismatch", lambda v: v.update(placement="single-worker"))
bad("unknown-placement", lambda v: v.update(placement="anywhere"))
for label, v in cases:
    result = helm(v)
    assert result.returncode != 0, f"unsafe core input accepted: {label}"
    print(f"negative core-{label}=PASS")
print(f"Core lint/determinism/2+2+2/peer roles/1,2,5,10 peers/placement/isolation=PASS negatives={len(cases)}")
