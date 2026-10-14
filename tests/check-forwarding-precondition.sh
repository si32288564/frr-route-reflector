#!/bin/sh
# Run on the authorized container-development host. No routing daemons launched.
set -eu
image=sha256:cc34cc1b8b4d93d8834472085f7d53792ad28cd97416319808a0fc3c1cd4f9ca
gate=$(cat "${1:?Path to container/forwarding-gate.sh}")
for initial in default zero; do
  if [ "$initial" = zero ]; then
    set -- --sysctl net.ipv4.ip_forward=0
  else
    set --
  fi
  echo "case=$initial"
  set +e
  timeout -s KILL 10 docker run --rm --network none \
    --memory 128m --pids-limit 32 \
    --cap-drop ALL --cap-add CHOWN --cap-add FOWNER --cap-add SETUID \
    --cap-add SETGID --cap-add NET_BIND_SERVICE --cap-add NET_ADMIN \
    --cap-add NET_RAW --cap-add SYS_ADMIN --security-opt no-new-privileges \
    "$@" --entrypoint /bin/sh "$image" -c '
      echo "before=$(cat /proc/sys/net/ipv4/ip_forward)"
      awk '\''$2 == "/proc/sys" { print }'\'' /proc/mounts
      set +e
      /bin/sh -c "$1"
      result=$?
      set -e
      echo "gate_exit=$result"
      echo "after=$(cat /proc/sys/net/ipv4/ip_forward)"
      exit "$result"
    ' gate "$gate"
  result=$?
  set -e
  echo "case_exit=$result"
  if [ "$initial" = default ]; then
    [ "$result" = 1 ] || exit 1
  else
    [ "$result" = 0 ] || exit 1
  fi
done
