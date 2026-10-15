#!/usr/bin/env python3
"""Finite smoke fixture derived from accepted Helm values, never a second RR SSOT."""
import hashlib
import ipaddress
import json
import pathlib
import subprocess

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[2]
IMAGE = "sha256:7acfef1c1e4fdf06c2f5d15383073ba3a9c78c24a52beee8d85da04e8102d47a"
CAPS = ["CHOWN", "SETUID", "SETGID", "NET_ADMIN", "NET_RAW", "NET_BIND_SERVICE", "SYS_ADMIN"]
PREFIXES = ["198.51.100.200/32", "198.51.100.201/32"]


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def render():
    values = json.loads((ROOT / "examples/documentation-values.json").read_text())
    raw = subprocess.check_output(["helm", "template", "rr", str(ROOT / "charts/frr-route-reflector"),
                                   "-f", str(ROOT / "examples/documentation-values.json")], text=True, timeout=20)
    objects = [o for o in yaml.safe_load_all(raw) if o]
    maps = {o["metadata"]["name"]: o["data"] for o in objects if o["kind"] == "ConfigMap"}
    assert len(maps) == 2 and len([o for o in objects if o["kind"] == "NetworkAttachmentDefinition"]) == 8
    routers, clients = [], []
    for index, rr in enumerate(values["routers"]):
        data = maps["rr-" + rr["name"]]
        assert data["frr.conf"].count("route-reflector-client") == 4
        assert "next-hop-self" not in data["frr.conf"]
        setup = ["ip link add eth0 type dummy", "ip link set eth0 up",
                 f"ip addr add 203.0.113.{index+2}/24 dev eth0"]
        for link in sorted(rr["links"], key=lambda l: l["interface"]):
            setup += [f"ip link add link eth0 name {link['interface']} type vlan id {link['vlanId']}",
                      f"ip link set {link['interface']} up",
                      f"ip addr add {link['localAddress']} dev {link['interface']}"]
        routers.append({"name": rr["name"], "loopback": rr["loopback"], "links": rr["links"],
                        "config": data, "config_sha256": sha(data["frr.conf"]),
                        "startup_only_shell": "; ".join(setup + ["exec /sbin/tini -- /usr/local/bin/entrypoint.sh"])})
    for index, client in enumerate(values["clients"][:2]):
        loopback = client["loopback"].split("/")[0]
        lines = ["frr defaults traditional", "hostname " + client["name"],
                 "service integrated-vtysh-config", "log stdout", "interface lo",
                 " ip ospf area " + values["cluster"]["ospfArea"], " ip ospf passive", "!"]
        links = []
        for rr_index, rr in enumerate(values["routers"], 1):
            link = next(l for l in rr["links"] if l["client"] == client["name"])
            assert ipaddress.ip_address(link["remoteAddress"]) in ipaddress.ip_interface(link["localAddress"]).network
            iface = "net" + str(rr_index)
            links.append({"interface": iface, "vlanId": link["vlanId"], "address": link["remoteAddress"] + "/31",
                          "rr": rr["name"], "rr_interface": link["interface"]})
            lines += ["interface " + iface, " ip ospf network point-to-point",
                      " ip ospf area " + values["cluster"]["ospfArea"], "!"]
        links.append({"interface": "net3", "vlanId": 1200, "address": f"203.0.113.{17+index}/29", "role": "client-only transit"})
        links.append({"interface": "net4", "vlanId": 1201+index, "address": f"203.0.113.{32+index*2}/31", "role": "unconnected padding for existing four-interface entrypoint"})
        lines += ["interface net3", " ip ospf network broadcast", " ip ospf area " + values["cluster"]["ospfArea"], "!",
                  "router ospf", " ospf router-id " + loopback, "!", "router bgp " + str(values["cluster"]["bgpAsn"]),
                  " bgp router-id " + loopback, " no bgp default ipv4-unicast"]
        for rr in values["routers"]:
            peer = rr["loopback"].split("/")[0]
            lines += [f" neighbor {peer} remote-as {values['cluster']['bgpAsn']}", f" neighbor {peer} update-source {loopback}"]
        lines += [" address-family ipv4 unicast", "  network " + PREFIXES[index]]
        for rr in values["routers"]:
            peer = rr["loopback"].split("/")[0]
            lines += [f"  neighbor {peer} activate", f"  neighbor {peer} next-hop-self"]
        lines += [" exit-address-family", "!"]
        text = "\n".join(lines) + "\n"
        clients.append({"name": client["name"], "loopback": client["loopback"], "prefix": PREFIXES[index],
                        "links": links, "config": text, "config_sha256": sha(text)})
    return {"source": "accepted-main Helm/example values", "image": IMAGE, "routers": routers, "clients": clients,
            "connected_execution": "BLOCKED: new isolated L2 fabric requires Owner approval", "g3": "NOT RUN"}


if __name__ == "__main__":
    print(json.dumps(render(), indent=2))
