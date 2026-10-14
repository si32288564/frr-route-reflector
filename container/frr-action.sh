#!/bin/sh
# watchfrr command adapter: standard helper stops as the daemon UID, starts as
# root (ospfd requires EUID 0 before invoking FRR's own privilege drop).
set -eu
action=${1:?}
daemon=${2:?}
case "$daemon" in all|mgmtd|zebra|bgpd|ospfd) ;; *) exit 1;; esac
stop_command="daemon_stop $daemon --reallyall"
[ "$daemon" != all ] || stop_command='all_stop --reallyall'
case "$action" in
  stop) exec su -s /bin/sh frr -c "/usr/lib/frr/watchfrr.sh $stop_command" ;;
  restart)
    su -s /bin/sh frr -c "/usr/lib/frr/watchfrr.sh $stop_command"
    exec /usr/lib/frr/watchfrr.sh start "$daemon" ;;
  *) exit 1;;
esac
