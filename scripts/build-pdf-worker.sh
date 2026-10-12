#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
LOCK_FILE="$ROOT_DIR/packaging/pdf-worker/runtime.lock"

if ! grep -q '"runtime_verified": true' "$LOCK_FILE"; then
  echo "PDF worker runtime lock is unverified; refusing to build." >&2
  exit 2
fi

exec podman build --pull=never --network=none \
  --file "$ROOT_DIR/packaging/pdf-worker/Containerfile" "$ROOT_DIR"
