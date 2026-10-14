#!/bin/sh
# Disposable diagnostic only; no production permission contract implied.
set -eu
image=${1:?Supply the built image ID}
docker run --rm --network none --cap-drop ALL \
  --cap-add NET_ADMIN --cap-add NET_RAW --cap-add SETUID --cap-add SETGID \
  --cap-add CHOWN --cap-add FOWNER --security-opt no-new-privileges \
  --cap-add NET_BIND_SERVICE \
  --sysctl net.ipv4.ip_forward=0 --entrypoint /bin/sh "$image" -c '
    set -eu
    id
    uname -m
    cat /proc/sys/net/ipv4/ip_forward
    sed -n "/^Cap/p; /^Seccomp/p; /^NoNewPrivs/p" /proc/self/status
    mkdir -p /var/tmp/frr /var/run/frr /var/lib/frr
    chmod 777 /var/tmp/frr /var/run/frr /var/lib/frr
    chown -R frr:frr /var/tmp/frr /var/run/frr /var/lib/frr
    failed=0
    for daemon in zebra ospfd bgpd mgmtd; do
      if [ ! -x /usr/lib/frr/$daemon ]; then
        printf "%s=not-packaged\n" "$daemon"
        continue
      fi
      /usr/lib/frr/$daemon --version
      set +e
      /usr/lib/frr/$daemon -d
      result=$?
      set -e
      printf "%s_exit=%s\n" "$daemon" "$result"
      [ "$result" -eq 0 ] || failed=1
    done
    sleep 2
    for process in /proc/[0-9]*/comm; do cat "$process" 2>/dev/null || :; done
    cat /proc/sys/net/ipv4/ip_forward
    exit "$failed"
  '
