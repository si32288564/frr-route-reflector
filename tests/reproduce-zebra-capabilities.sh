#!/bin/sh
# Run on the container development host. No host networking or host sysctls.
set -eu
image=quay.io/frrouting/frr@sha256:f90d26a9fd5c14fc5795a73b4254ac88bc3186c45bbeb220a225fb6182de812c
docker run --rm --network none --cap-drop ALL \
  --cap-add NET_ADMIN --cap-add NET_RAW --cap-add SETUID \
  --cap-add SETGID --cap-add CHOWN --cap-add FOWNER \
  --sysctl net.ipv4.ip_forward=0 --entrypoint /bin/sh "$image" -c '
    set -e
    mkdir -p /var/tmp/frr /var/run/frr /var/lib/frr
    chmod 777 /var/tmp/frr /var/run/frr /var/lib/frr
    chown -R frr:frr /var/tmp/frr /var/run/frr /var/lib/frr
    /usr/lib/frr/zebra --version
    cat /proc/sys/net/ipv4/ip_forward
    set +e
    /usr/lib/frr/zebra -d
    result=$?
    printf "zebra_exit=%s\n" "$result"
    exit "$result"
  '
