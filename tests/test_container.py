"""Disposable namespace implementation test, never touches Kubernetes."""
import json
import pathlib
import subprocess
import tempfile
import time
import uuid
import signal
import sys

import yaml

IMAGE = "frr-task0001:implementation"
signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(SystemExit(124)))
CAPS = ["CHOWN", "SETUID", "SETGID", "NET_ADMIN", "NET_RAW", "NET_BIND_SERVICE", "SYS_ADMIN"]


def run(*args, check=True):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, check=check, timeout=45)


objects = list(yaml.safe_load_all(run("helm", "template", "rr", "charts/frr-route-reflector",
                                    "-f", "examples/documentation-values.json").stdout))
cm = next(o for o in objects if o and o["kind"] == "ConfigMap")
name = "frr-implementation-" + uuid.uuid4().hex
setup = "ip link show eth0 >/dev/null 2>&1 || ip link add eth0 type dummy; ip link set eth0 up; ip addr replace 203.0.113.2/24 dev eth0; "
for i, line in enumerate(cm["data"]["links"].splitlines(), 1):
    if "--missing-interface" in sys.argv and i == 4:
        continue
    iface, addr = line.split()
    setup += f"ip link show {iface} >/dev/null 2>&1 || ip link add link eth0 name {iface} type vlan id {1100+i}; ip link set {iface} up; ip addr replace {addr} dev {iface}; "
setup += "exec /sbin/tini -- /usr/local/bin/entrypoint.sh"
opts = ["docker", "create", "--name", name, "--network", "none", "--group-add", "102", "--memory", "256m",
        "--pids-limit", "128", "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
        "--sysctl", "net.ipv4.ip_forward=0"]
for cap in CAPS:
    opts += ["--cap-add", cap]
try:
    run(*opts, "--entrypoint", "/bin/sh", IMAGE, "-ec", setup)
    with tempfile.TemporaryDirectory() as tmp:
        for key, value in cm["data"].items():
            pathlib.Path(tmp, key).write_text(value)
        run("docker", "cp", tmp + "/.", name + ":/config/")
    run("docker", "start", name)
    ready = False
    for _ in range(35):
        probe = run("docker", "exec", name, "/usr/local/bin/health.sh", check=False)
        if probe.returncode == 0:
            ready = True
            break
        if not json.loads(run("docker", "inspect", name).stdout)[0]["State"]["Running"]:
            break
        time.sleep(1)
    print(run("docker", "logs", name, check=False).stdout)
    if "--missing-interface" in sys.argv:
        assert not ready
        state = json.loads(run("docker", "inspect", name).stdout)[0]["State"]
        assert not state["Running"] and state["ExitCode"] == 1
        assert "WATCHFRR" not in run("docker", "logs", name).stdout
        print("missing-interface-refusal=PASS")
        sys.exit(0)
    if not ready:
        print("last_probe=" + probe.stdout)
        print(run("docker", "exec", name, "/bin/sh", "-x", "/usr/local/bin/health.sh", "--starting", check=False).stdout)
    assert ready, "startup/readiness did not pass"
    print("startup=PASS")
    syntax = run("docker", "exec", name, "vtysh", "-C", "-f", "/etc/frr/frr.conf")
    print("syntax_command=vtysh -C -f /etc/frr/frr.conf\n" + syntax.stdout)
    assert "Unknown command" not in syntax.stdout
    print("syntax_exit=" + str(syntax.returncode))
    for config in [o for o in objects if o and o["kind"] == "ConfigMap"]:
        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write(config["data"]["frr.conf"])
            f.flush()
            pathlib.Path(f.name).chmod(0o644)
            run("docker", "cp", f.name, name + ":/tmp/check.conf")
        syntax = run("docker", "exec", name, "vtysh", "-C", "-f", "/tmp/check.conf")
        assert "Unknown command" not in syntax.stdout
        print(config["metadata"]["name"] + " syntax_exit=0 output=" + repr(syntax.stdout))
    print(run("docker", "exec", name, "/bin/sh", "-c",
              "for d in watchfrr mgmtd zebra ospfd bgpd; do p=$(cat /run/frr/$d.pid); echo daemon=$d; sed -n '/^Uid/p; /^Gid/p; /^Cap/p; /^NoNewPrivs/p; /^Seccomp/p' /proc/$p/status; done").stdout)
    for command in ["show running-config", "show ip ospf", "show bgp ipv4 unicast summary"]:
        result = run("docker", "exec", name, "vtysh", "-c", command)
        print(result.stdout)
        assert "% Unknown" not in result.stdout
    running = run("docker", "exec", name, "vtysh", "-c", "show running-config").stdout
    assert "bgp no-rib" in running and "max-metric router-lsa administrative" in running
    assert running.count("route-reflector-client") == 4
    assert "next-hop-self" not in running
    assert run("docker", "exec", name, "cat", "/etc/frr/frr.conf").stdout == cm["data"]["frr.conf"]
    assert run("docker", "exec", name, "cat", "/proc/sys/net/ipv4/ip_forward").stdout.strip() == "0"
    assert cm["data"]["loopback"] in run("docker", "exec", name, "ip", "-4", "-o", "addr", "show", "dev", "lo").stdout
    print("integrated-config=PASS forwarding-readback=0")
    if "--drift" in sys.argv:
        # Only the disposable Docker sandbox netns, never the host netns.
        pid = str(json.loads(run("docker", "inspect", name).stdout)[0]["State"]["Pid"])
        run("sudo", "-n", "nsenter", "-t", pid, "-n", "sysctl", "-w", "net.ipv4.ip_forward=1")
        for _ in range(50):
            if not json.loads(run("docker", "inspect", name).stdout)[0]["State"]["Running"]:
                break
            time.sleep(0.1)
        else:
            raise AssertionError("forwarding drift did not terminate routing/container")
        print("drift-stop=PASS")
    else:
        with tempfile.NamedTemporaryFile(mode="w") as f:
            f.write("hostname unauthorized-runtime-edit\n")
            f.flush()
            run("docker", "cp", f.name, name + ":/etc/frr/frr.conf")
        run("docker", "restart", "--time", "15", name)
        for _ in range(35):
            if run("docker", "exec", name, "/usr/local/bin/health.sh", check=False).returncode == 0:
                break
            time.sleep(1)
        else:
            raise AssertionError("container restart failed")
        assert run("docker", "exec", name, "cat", "/etc/frr/frr.conf").stdout == cm["data"]["frr.conf"]
        assert run("docker", "exec", name, "cat", "/proc/sys/net/ipv4/ip_forward").stdout.strip() == "0"
        print("restart-discards-runtime-edit=PASS")
        run("docker", "stop", "--time", "15", name)
    state = json.loads(run("docker", "inspect", name).stdout)[0]["State"]
    print("stop-state=" + json.dumps(state))
    assert state["ExitCode"] == (1 if "--drift" in sys.argv else 0)
finally:
    print(run("docker", "logs", name, check=False).stdout)
    cleanup = run("docker", "rm", "-f", name, check=False)
    print("cleanup_exit=" + str(cleanup.returncode))
    assert not run("docker", "ps", "-aq", "--filter", "name=^/" + name + "$").stdout.strip()
