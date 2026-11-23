#!/bin/bash
set -euo pipefail
validate_inactive_tunl0() {
  local link addresses flags
  link=$(ip -o link show dev tunl0) || return 1
  [[ "$link" =~ \<([^\>]*)\> ]] || return 1
  flags=${BASH_REMATCH[1]}
  case ",$flags," in *,UP,*) return 1 ;; esac
  [[ "$link" == *" state DOWN "* ]] || return 1
  addresses=$(ip -4 -o addr show dev tunl0) || return 1
  [[ -z "$addresses" ]] || return 1
  addresses=$(ip -6 -o addr show dev tunl0) || return 1
  [[ -z "$addresses" ]]
}
validate_interface_inventory() {
  local count=$1 actual=$2 i
  case "$count" in 1|4) ;; *) return 1 ;; esac
  local expected=(eth0 lo)
  for ((i=1; i<=count; i++)); do expected+=("net$i"); done
  if test "$actual" = "$(printf '%s\n' "${expected[@]}" | sort | tr '\n' ' ')"; then
    return 0
  fi
  expected+=(tunl0)
  test "$actual" = "$(printf '%s\n' "${expected[@]}" | sort | tr '\n' ' ')" || return 1
  validate_inactive_tunl0
}
stop() {
  trap - EXIT TERM INT
  rm -f /run/frr/boot-complete
  # watchfrr/frrcommon own daemon lifecycle, tini reaps orphaned children.
  if [ -n "${watchpid:-}" ]; then
    kill -TERM "$watchpid" 2>/dev/null || true
    wait "$watchpid" 2>/dev/null || true
  fi
  if [ -r /etc/frr/daemons ]; then
    timeout 10 /usr/local/bin/frr-action.sh stop all || true
  fi
}
trap 'rc=$?; printf "STOP: entrypoint line %s failed (exit %s)\n" "$LINENO" "$rc" >&2' ERR
trap stop EXIT
trap 'exit 0' TERM INT
rm -f /run/frr/boot-complete /run/frr/*.pid /run/frr/*.vty
/usr/local/bin/forwarding-gate.sh
test "$(id -u)" = 0
test -r /config/frr.conf
test -r /config/links
test -r /config/loopback
mapfile -t links < /config/links
inventory=$(ls /sys/class/net | sort | tr '\n' ' ')
validate_interface_inventory "${#links[@]}" "$inventory" || {
  echo "STOP: interface inventory or tunl0 inactivity check failed: $inventory" >&2
  exit 1
}
ip -4 addr show dev eth0 | grep -q 'inet '
for ((i=0; i<${#links[@]}; i++)); do
  read -r iface address <<< "${links[$i]}"
  test "$iface" = "net$((i+1))"
  ip -d link show dev "$iface" | grep -q 'vlan protocol 802.1Q'
  ip -4 -o addr show dev "$iface" | awk '{print $4}' | grep -Fxq "$address"
done
# Entrypoint is the sole stable-loopback owner; FRR only advertises it.
loopback=$(cat /config/loopback)
[[ "$loopback" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+/32$ ]]
ip addr replace "$loopback" dev lo
ip link set lo up
rm -f /etc/frr/frr.conf /etc/frr/daemons
cp /config/frr.conf /etc/frr/frr.conf
cp /usr/share/rr/daemons /etc/frr/daemons
chmod 640 /etc/frr/frr.conf /etc/frr/daemons
chown frr:frr /etc/frr/frr.conf /etc/frr/daemons
/usr/local/bin/forwarding-gate.sh
/usr/lib/frr/watchfrr \
  -r '/usr/local/bin/frr-action.sh restart %s' \
  -k '/usr/local/bin/frr-action.sh stop %s' \
  mgmtd zebra bgpd ospfd &
watchpid=$!
# The startup gate also waits for standard vty sockets/config application.
for attempt in {1..30}; do
  /usr/local/bin/forwarding-gate.sh
  if /usr/local/bin/health.sh --starting >/dev/null 2>&1 && vtysh -c 'show ip ospf' >/dev/null 2>&1; then
    vtysh -b
    touch /run/frr/boot-complete
    break
  fi
  sleep 1
done
test -f /run/frr/boot-complete
while :; do
  /usr/local/bin/forwarding-gate.sh || exit 1
  /usr/local/bin/health.sh >/dev/null 2>&1 || exit 1
  sleep 1 & wait $!
done
