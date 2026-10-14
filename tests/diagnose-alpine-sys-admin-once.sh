#!/bin/sh
# One authorized execution only: PR #6 issuecomment-6180314494.
# Re-execution requires fresh authorization. Never use this for release Pods.
set -eu
image=sha256:cc34cc1b8b4d93d8834472085f7d53792ad28cd97416319808a0fc3c1cd4f9ca
[ "$(docker image inspect "$image" --format '{{.Architecture}}')" = arm64 ]
command -v timeout >/dev/null
name=frr-diag-$(cat /proc/sys/kernel/random/uuid)
if docker container inspect "$name" >/dev/null 2>&1; then
  echo name_collision; exit 1
fi
started=$(date +%s)
owned=0
cleanup() {
  result=$?
  trap - EXIT HUP INT TERM
  set +e
  if [ "$owned" = 1 ]; then
    timeout -s KILL 4 docker rm -f "$name"
    cleanup_rc=$?
    echo "cleanup_exit=$cleanup_rc"
    remaining=$(timeout -s KILL 2 docker ps -aq --filter "name=^/${name}$")
    query_rc=$?
    if [ "$query_rc" = 0 ] && [ -z "$remaining" ]; then
      echo container_absent=PASS
    else
      echo container_absent=FAIL
      result=1
    fi
    [ "$cleanup_rc" = 0 ] || result=1
  fi
  echo "total_elapsed_seconds=$(($(date +%s) - started))"
  echo "script_exit=$result"
  exit "$result"
}
trap cleanup EXIT
trap 'exit 130' HUP INT TERM
echo "container_name=$name image=$image"
for ns in net pid ipc; do
  printf "host_%s=" "$ns"; readlink /proc/self/ns/$ns
done
# Create while stopped; no daemon is exposed before the external timer starts.
docker create --name "$name" --network none --ipc private \
  --memory 256m --memory-swap 256m --pids-limit 64 \
  --cap-drop ALL --cap-add CHOWN --cap-add FOWNER --cap-add SETUID \
  --cap-add SETGID --cap-add NET_BIND_SERVICE --cap-add NET_ADMIN \
  --cap-add NET_RAW --cap-add SYS_ADMIN --security-opt no-new-privileges \
  --sysctl net.ipv4.ip_forward=0 --entrypoint /bin/sh "$image" -c '
    set -eu
    check_forwarding() {
      value=$(cat /proc/sys/net/ipv4/ip_forward)
      echo "forwarding_$1=$value"
      [ "$value" = 0 ] || exit 90
    }
    id
    uname -m
    for ns in net pid ipc mnt user uts; do
      printf "%s=" "$ns"; readlink /proc/self/ns/$ns
    done
    sed -n "/^Cap/p; /^Seccomp/p; /^NoNewPrivs/p" /proc/self/status
    check_forwarding before
    mkdir -p /var/tmp/frr /var/run/frr /var/lib/frr
    chmod 777 /var/tmp/frr /var/run/frr /var/lib/frr
    chown -R frr:frr /var/tmp/frr /var/run/frr /var/lib/frr
    failed=0
    # Management backend first; do not invent a routing supervisor.
    for daemon in mgmtd zebra ospfd bgpd; do
      /usr/lib/frr/$daemon --version
      echo "command=/usr/lib/frr/$daemon -d --log stdout"
      set +e
      /usr/lib/frr/$daemon -d --log stdout > /tmp/$daemon.log 2>&1
      result=$?
      set -e
      echo "${daemon}_launch_exit=$result"
      cat /tmp/$daemon.log
      [ "$result" = 0 ] || failed=1
      check_forwarding after_$daemon
    done
    for round in 1 2 3; do
      sleep 1
      check_forwarding during_$round
    done
    for daemon in mgmtd zebra ospfd bgpd; do
      found=0
      for comm in /proc/[0-9]*/comm; do
        [ -r "$comm" ] || continue
        [ "$(cat "$comm")" = "$daemon" ] || continue
        found=1
        proc=${comm%/comm}
        echo "${daemon}_process=${proc##*/}"
        sed -n "/^State/p; /^Uid/p; /^Gid/p; /^Cap/p; /^Seccomp/p; /^NoNewPrivs/p" "$proc/status"
      done
      echo "${daemon}_present=$found"
      [ "$found" = 1 ] || failed=1
      cat /tmp/$daemon.log
    done
    for comm in /proc/[0-9]*/comm; do
      [ -r "$comm" ] || continue
      case "$(cat "$comm")" in
        mgmtd|zebra|ospfd|bgpd)
          proc=${comm%/comm}
          # Signal as the daemon account; CAP_KILL is not approved.
          su -s /bin/sh frr -c "kill -TERM ${proc##*/}"
          echo "term_sent=${proc##*/}" ;;
      esac
    done
    sleep 2
    for daemon in mgmtd zebra ospfd bgpd; do
      cat /tmp/$daemon.log
    done
    for comm in /proc/[0-9]*/comm; do
      [ -r "$comm" ] || continue
      case "$(cat "$comm")" in
        mgmtd|zebra|ospfd|bgpd)
          proc=${comm%/comm}
          echo "after_term=${proc##*/}"
          sed -n "/^State/p" "$proc/status" ;;
      esac
    done
    check_forwarding final
    exit "$failed"
  '
owned=1
docker inspect "$name" --format '{{json .HostConfig}}'
set +e
# Hard kill at 55s reserves time for outer forced removal, within the 60s bound.
timeout -s KILL 55 docker start -a "$name"
diagnostic_rc=$?
set -e
echo "diagnostic_exit=$diagnostic_rc"
docker inspect "$name" --format 'container_exit={{.State.ExitCode}} running={{.State.Running}} oom={{.State.OOMKilled}}'
exit "$diagnostic_rc"
