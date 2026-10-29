#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
LOCK_FILE="$ROOT_DIR/packaging/pdf-worker/runtime.lock"
APP_ROOT=${REDACTION_LAB_HOME:-"$HOME/Library/Application Support/RedactionLab"}
RUNTIME_ROOT="$APP_ROOT/runtime/pdf-worker"
PODMAN="$RUNTIME_ROOT/podman/bin/podman"
STATE="$RUNTIME_ROOT/state"
PYTHON="$ROOT_DIR/.venv/bin/python"

test -f "$LOCK_FILE"
test -x "$PODMAN"
test -x "$PYTHON"
test -d "$ROOT_DIR/packaging/pdf-worker/wheelhouse"

expected_digest=$("$PYTHON" -I -c 'import json,sys; print(json.load(open(sys.argv[1]))["podman_executable_sha256"])' "$LOCK_FILE")
observed_digest=sha256:$(shasum -a 256 "$PODMAN" | awk '{print $1}')
test "$observed_digest" = "$expected_digest"

export HOME="$RUNTIME_ROOT"
export XDG_CONFIG_HOME="$STATE/config"
export XDG_DATA_HOME="$STATE/data"
export XDG_RUNTIME_DIR="$STATE/tmp"
export CONTAINERS_CONF="$RUNTIME_ROOT/containers.conf"

exec "$PODMAN" --connection redaction-lab-pdf-v1 build \
  --pull=never --network=none \
  --tag localhost/redaction-lab/pdf-worker:qualification \
  --file "$ROOT_DIR/packaging/pdf-worker/Containerfile" "$ROOT_DIR"
