#!/bin/sh
# The runtime namespace must be non-forwarding before any routing service starts.
# No host fallback, remount, unsafe-sysctl admission change or silent downgrade.
set -eu
value=$(cat /proc/sys/net/ipv4/ip_forward) || exit 1
if [ "$value" != 0 ]; then
  sysctl -w net.ipv4.ip_forward=0 || {
    echo 'STOP: cannot disable IPv4 forwarding in this network namespace' >&2
    exit 1
  }
fi
[ "$(cat /proc/sys/net/ipv4/ip_forward)" = 0 ] || {
  echo 'STOP: IPv4 forwarding safety readback failed' >&2
  exit 1
}
