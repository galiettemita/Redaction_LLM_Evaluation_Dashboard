#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
LOCK_FILE="$ROOT_DIR/packaging/pdf-worker/runtime.lock"

if ! grep -q '"runtime_verified": true' "$LOCK_FILE"; then
  echo "PDF worker runtime lock is unverified; refusing runtime verification." >&2
  exit 2
fi

echo "Run clean-device canaries with --pull=never --network=none, no mounts, a read-only root, and the exact locked image." >&2
exit 2
