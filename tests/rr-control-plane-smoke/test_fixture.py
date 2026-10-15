#!/usr/bin/env python3
"""Static fixture tests only: never claim BGP/OSPF/packet proof."""
import ipaddress
import json
import pathlib
import subprocess
import sys
import tempfile

from fixture import ROOT, PREFIXES, render, sha

first = render()
assert first == render(), "nondeterministic fixture"
values = json.loads((ROOT / "examples/documentation-values.json").read_text())
assert len(first["routers"]) == len(first["clients"]) == 2
for router in first["routers"]:
    assert len(router["links"]) == 4
    assert router["config_sha256"] == sha(router["config"]["frr.conf"])
    assert len(router["config"]["links"].splitlines()) == 4
    assert "bgp no-rib\n" in router["config"]["frr.conf"]
    for other in first["routers"]:
        assert "neighbor " + other["loopback"].split("/")[0] + " " not in router["config"]["frr.conf"]
    for client in values["clients"]:
        assert "neighbor " + client["loopback"].split("/")[0] in router["config"]["frr.conf"]
for client in first["clients"]:
    assert client["config_sha256"] == sha(client["config"])
    assert client["prefix"] in PREFIXES and "force" not in client["config"]
    assert "route-reflector-client" not in client["config"]
    assert len(client["links"]) == 4
    for link in client["links"][:2]:
        rr = next(r for r in first["routers"] if r["name"] == link["rr"])
        parent = next(l for l in rr["links"] if l["interface"] == link["rr_interface"])
        assert parent["client"] == client["name"] and parent["vlanId"] == link["vlanId"]
        net = ipaddress.ip_interface(parent["localAddress"]).network
        assert ipaddress.ip_interface(link["address"]).network == net
        assert ipaddress.ip_interface(link["address"]).ip != ipaddress.ip_interface(parent["localAddress"]).ip
    assert client["links"][2]["vlanId"] == 1200
    assert str(ipaddress.ip_interface(client["links"][2]["address"]).network) == "203.0.113.16/29"
assert not any(l["vlanId"] == 1200 for r in first["routers"] for l in r["links"])
with tempfile.TemporaryDirectory() as tmp:
    out = pathlib.Path(tmp) / "must-not-exist.json"
    attempt = subprocess.run([sys.executable, str(pathlib.Path(__file__).with_name("startup.py")),
                              "--connected", "--output", str(out)], capture_output=True, text=True, timeout=10)
    assert attempt.returncode == 78 and "STOP before Docker" in attempt.stdout
    assert not out.exists()
print("PASS static: deterministic Helm-derived 2-RR/2-Client fixture, retained 4 peers/4 links per RR")
print("PASS static: /31 counterpart/VLAN mapping, client-only /29, no RR-RR peer, connected execution fails closed")
print("BGP reflection/NEXT_HOP/learned-route FIB/packet non-transit/G-3 = NOT RUN")
record = pathlib.Path(__file__).with_name("measured-startup.json")
if record.exists():
    measured = json.loads(record.read_text())
    assert len(measured["routers"]) == 2 and "stop" not in measured
    for rr in measured["routers"]:
        assert rr["actual_config_sha256"] == rr["desired_config_sha256"]
        assert rr["forwarding"] == "0" and rr["normal_stop_exit"] == 0
        assert rr["bgp_summary"]["peerCount"] == 4 and rr["bgp_summary"]["ribCount"] == 0
        assert all(p["state"] == "Idle" for p in rr["bgp_summary"]["peers"].values())
        assert rr["isolation"]["NetworkMode"] == "none" and not rr["mounts"]
    assert all(c["absent"] and c["remove_exit"] == 0 for c in measured["cleanup"])
    assert all(c["exit"] == 0 for c in measured["client_syntax"])
    assert all(measured[k] == "NOT RUN" for k in ("live_reflection", "next_hop_updates", "learned_route_fib_exclusion", "packet_nontransit", "rr_loss_with_survivor", "g3"))
    print("PASS offline measured-startup record consistency only; no live acceptance inferred")
