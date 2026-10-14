#!/bin/sh
# The runtime namespace must be non-forwarding before any routing service starts.
# No host fallback, remount, unsafe-sysctl admission change or silent downgrade.
set -eu
# Calico owns initialization. The container never writes/remounts proc sysctls.
[ "$(cat /proc/sys/net/ipv4/ip_forward)" = 0 ] || {
  echo 'STOP: IPv4 forwarding safety readback failed' >&2
  exit 1
}
