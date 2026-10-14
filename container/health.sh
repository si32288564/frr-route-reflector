#!/bin/sh
set -eu
/usr/local/bin/forwarding-gate.sh
if [ "${1:-}" != --starting ]; then test -f /run/frr/boot-complete; fi
for daemon in watchfrr mgmtd zebra ospfd bgpd; do
  pid=$(cat /run/frr/$daemon.pid)
  test "$(cat /proc/$pid/comm)" = "$daemon"
  ! grep -q '^State:.*Z' /proc/$pid/status
done
