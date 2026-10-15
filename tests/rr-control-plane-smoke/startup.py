#!/usr/bin/env python3
"""Only already-authorized G-2 network-none startup. Connected mode fails closed.

Run under external timeout 165s + 15s kill grace. No new network, host namespace
entry, bridge, route, mount, installation, rebuild or target peers are created.
"""
import argparse
import datetime
import json
import pathlib
import signal
import subprocess
import tempfile
import time
import uuid

from fixture import CAPS, IMAGE, PREFIXES, render, sha


def run(*args, check=True, timeout=15):
    return subprocess.run(args, capture_output=True, text=True, check=check, timeout=timeout)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--connected", action="store_true")
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()
    if args.connected:
        print("STOP before Docker: connected fixture needs explicitly approved new isolated L2 fabric")
        return 78
    report = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "commands": [], "routers": [],
              "live_reflection": "NOT RUN", "next_hop_updates": "NOT RUN", "learned_route_fib_exclusion": "NOT RUN",
              "packet_nontransit": "NOT RUN", "rr_loss_with_survivor": "NOT RUN", "g3": "NOT RUN"}
    owned = {}
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(SystemExit(124)))
    signal.signal(signal.SIGINT, lambda *_: (_ for _ in ()).throw(SystemExit(130)))
    code = 0
    try:
        spec = render()
        report["fixture"] = spec
        image = json.loads(run("docker", "image", "inspect", IMAGE).stdout)[0]
        assert image["Id"] == IMAGE and image["Architecture"] == "arm64"
        report["image"] = {"id": image["Id"], "architecture": image["Architecture"], "size": image["Size"]}
        report["tools"] = {"docker": run("docker", "version", "--format", "{{.Server.Version}}").stdout.strip(),
                           "helm": run("helm", "version", "--short").stdout.strip()}
        for rr in spec["routers"]:
            name = "frr-rr-smoke-" + uuid.uuid4().hex + "-" + rr["name"]
            before = run("docker", "container", "inspect", name, check=False)
            assert before.returncode == 1 and "No such container" in before.stderr
            opts = ["docker", "create", "--pull", "never", "--platform", "linux/arm64", "--name", name,
                    "--label", "rr-smoke-owned=" + name, "--network", "none", "--group-add", "102",
                    "--memory", "256m", "--memory-swap", "256m", "--pids-limit", "128",
                    "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--sysctl", "net.ipv4.ip_forward=0"]
            for cap in CAPS:
                opts += ["--cap-add", cap]
            opts += ["--entrypoint", "/bin/sh", IMAGE, "-ec", rr["startup_only_shell"]]
            report["commands"].append(opts)
            owned[name] = None
            cid = run(*opts).stdout.strip()
            owned[name] = cid
            with tempfile.TemporaryDirectory(prefix="rr-smoke-config-") as tmp:
                for key, value in rr["config"].items():
                    pathlib.Path(tmp, key).write_text(value)
                run("docker", "cp", tmp + "/.", name + ":/config/")
            run("docker", "start", name)
            report["routers"].append({"name": rr["name"], "container": name, "container_id": cid,
                                      "desired_config_sha256": rr["config_sha256"]})
        deadline = time.monotonic() + 40
        while time.monotonic() < deadline:
            if all(run("docker", "exec", r["container"], "/usr/local/bin/health.sh", check=False).returncode == 0 for r in report["routers"]):
                break
            time.sleep(1)
        else:
            raise RuntimeError("G-2 startup timeout; no isolation relaxation permitted")
        for rr in report["routers"]:
            name = rr["container"]
            inspected = json.loads(run("docker", "container", "inspect", name).stdout)[0]
            hc = inspected["HostConfig"]
            rr["isolation"] = {k: hc[k] for k in ("NetworkMode", "PidMode", "IpcMode", "Privileged", "CapDrop", "CapAdd", "SecurityOpt", "Memory", "MemorySwap", "PidsLimit", "Binds", "Devices")}
            rr["mounts"] = inspected["Mounts"]
            assert hc["NetworkMode"] == "none" and not hc["Privileged"] and not hc["Binds"] and not hc["Devices"], "unexpected isolation"
            assert not inspected["Mounts"], "unexpected mount"
            normalize = lambda cap: cap.removeprefix("CAP_")
            assert [normalize(c) for c in hc["CapDrop"]] == ["ALL"], "not drop ALL"
            assert {normalize(c) for c in hc["CapAdd"]} == set(CAPS), "unexpected capability set"
            actual = run("docker", "exec", name, "cat", "/etc/frr/frr.conf").stdout
            assert sha(actual) == rr["desired_config_sha256"]
            rr["actual_config_sha256"] = sha(actual)
            rr["running_config"] = run("docker", "exec", name, "vtysh", "-c", "show running-config").stdout
            assert "bgp no-rib" in rr["running_config"] and rr["running_config"].count("route-reflector-client") == 4
            rr["forwarding"] = run("docker", "exec", name, "cat", "/proc/sys/net/ipv4/ip_forward").stdout.strip()
            assert rr["forwarding"] == "0"
            rr["bgp_summary"] = json.loads(run("docker", "exec", name, "vtysh", "-c", "show bgp ipv4 unicast summary json").stdout)
            rr["kernel_routes"] = json.loads(run("docker", "exec", name, "ip", "-4", "-j", "route", "show", "table", "all").stdout)
            assert not {p for p in PREFIXES} & {r.get("dst") for r in rr["kernel_routes"]}
            rr["ospf_neighbors"] = run("docker", "exec", name, "vtysh", "-c", "show ip ospf neighbor").stdout
            rr["frr_version"] = run("docker", "exec", name, "vtysh", "-c", "show version").stdout
            rr["bgpd_process"] = run("docker", "exec", name, "/bin/sh", "-ec",
                'p=$(cat /run/frr/bgpd.pid); test "$(cat /proc/$p/comm)" = bgpd; sed -n "/^Uid:/p; /^Gid:/p; /^Cap/p; /^NoNewPrivs:/p; /^Seccomp:/p" /proc/$p/status').stdout
            rr["startup"] = "PASS G-2 isolated startup only"
            rr["fib_baseline"] = "No test service prefixes; vacuous without learned BGP routes, NOT a no-rib behavior PASS"
        report["client_syntax"] = []
        for client in spec["clients"]:
            with tempfile.NamedTemporaryFile(mode="w", prefix="rr-smoke-client-") as tmp:
                tmp.write(client["config"])
                tmp.flush()
                pathlib.Path(tmp.name).chmod(0o644)
                run("docker", "cp", tmp.name, report["routers"][0]["container"] + ":/tmp/client-check.conf")
            checked = run("docker", "exec", report["routers"][0]["container"], "vtysh", "-C", "-f", "/tmp/client-check.conf")
            assert not checked.stdout.strip() and not checked.stderr.strip(), "unexpected FRR dry-run diagnostic"
            report["client_syntax"].append({"client": client["name"], "exit": checked.returncode,
                                             "stdout": checked.stdout, "stderr": checked.stderr,
                                             "scope": "syntax only; client NOT started"})
        for rr in report["routers"]:
            name = rr["container"]
            run("docker", "stop", "--time", "10", name)
            state = json.loads(run("docker", "container", "inspect", name).stdout)[0]["State"]
            rr["normal_stop_exit"] = state["ExitCode"]
            assert state["ExitCode"] == 0
    except (Exception, SystemExit) as exc:
        code = 1
        report["stop"] = type(exc).__name__ + ": " + str(exc)
    finally:
        cleanup = []
        for name, cid in owned.items():
            try:
                inspect = run("docker", "container", "inspect", name, check=False, timeout=5)
                if inspect.returncode == 0:
                    obj = json.loads(inspect.stdout)[0]
                    assert obj["Config"]["Labels"].get("rr-smoke-owned") == name
                    assert cid is None or obj["Id"] == cid
                    entry = next((r for r in report["routers"] if r["container"] == name), None)
                    if entry is not None:
                        entry["final_state"] = {k: obj["State"][k] for k in ("Running", "ExitCode", "OOMKilled", "Error")}
                        entry["logs"] = run("docker", "logs", "--tail", "80", name, check=False, timeout=5).stdout
                    removed = run("docker", "rm", "-f", name, check=False, timeout=5).returncode
                else:
                    removed = None
                absent = run("docker", "container", "inspect", name, check=False, timeout=5)
                valid = absent.returncode == 1 and "No such container" in absent.stderr
                cleanup.append({"name": name, "remove_exit": removed, "absence_exit": absent.returncode, "absent": valid})
                if not valid:
                    code = 1
            except Exception as exc:
                cleanup.append({"name": name, "error": str(exc), "absent": False})
                code = 1
        report["cleanup"] = cleanup
        report["ended_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"exit": code, "rr_startups": [r.get("startup", "NOT RUN") for r in report["routers"]],
                      "live_reflection": report["live_reflection"], "cleanup": cleanup}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
