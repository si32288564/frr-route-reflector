FROM alpine:3.24@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6
RUN apk add --no-cache frr=10.6.1-r0 tini=0.19.0-r3 \
 && mkdir -p /run/frr /var/tmp/frr /config /lib/frr \
 && chown -R frr:frr /etc/frr /run/frr /var/tmp/frr /lib/frr \
 && chmod 775 /etc/frr /run/frr /var/tmp/frr /lib/frr
COPY --chmod=755 entrypoint.sh frr-action.sh forwarding-gate.sh health.sh /usr/local/bin/
COPY --chown=frr:frr daemons /etc/frr/daemons
COPY daemons /usr/share/rr/daemons
USER 0:101
ENTRYPOINT ["/sbin/tini", "--", "/usr/local/bin/entrypoint.sh"]
