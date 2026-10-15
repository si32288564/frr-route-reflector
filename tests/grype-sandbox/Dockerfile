# Task 0004 reviewed recovery plan. NOT BUILT: DB-size preflight STOP.
# Supply only the enumerated, hash-verified inputs in a unique temporary context.
FROM alpine:3.24@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6
COPY --chmod=0555 grype /work/grype
COPY --chmod=0444 db.tar.zst amd64.tar arm64.tar /work/
COPY --chmod=0555 init.sh /work/init.sh
ENV HOME=/tmp GRYPE_DB_CACHE_DIR=/tmp/grype-db GRYPE_DB_AUTO_UPDATE=false GRYPE_CHECK_FOR_APP_UPDATE=false
ENV GRYPE_DB_VALIDATE_BY_HASH_ON_START=true GRYPE_DB_VALIDATE_AGE=true GRYPE_DB_MAX_ALLOWED_BUILT_AGE=120h
USER 65534:65534
ENTRYPOINT ["/work/init.sh"]
