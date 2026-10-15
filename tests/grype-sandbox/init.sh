#!/bin/sh
# Task-owned initialization only. Never execute programs from target archives.
# This plan is NOT RUN: the actual DB exceeds the approved memory/tmpfs budget.
set -eu
case "${1:-}" in
    amd64|arm64) arch=$1 ;;
    *) echo 'Expected one frozen archive architecture: amd64 or arm64' >&2; exit 64 ;;
esac
[ "$#" -eq 1 ] || exit 64
/work/grype version >&2
sha256sum /work/db.tar.zst >&2
# Standard v0.120.1 CLI; no invented import metadata or disabled validations.
/work/grype db import /work/db.tar.zst >&2
/work/grype db status -o json >&2
exec /work/grype "docker-archive:/work/$arch.tar" -o json --fail-on high
