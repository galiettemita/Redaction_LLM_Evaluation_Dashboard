#!/bin/sh
set -eu

ROOT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PYTHON="$ROOT_DIR/.venv/bin/python"

if ! test -x "$PYTHON"; then
  echo "Frozen project environment is unavailable." >&2
  exit 2
fi

export PYTHONPATH="$ROOT_DIR/src"
exec "$PYTHON" - <<'PY'
from pathlib import Path
from tempfile import TemporaryDirectory

from redaction_lab.application.isolation import ApplicationPdfWorker
from redaction_lab.application.worker_protocol import WorkerStatus
from redaction_lab.contracts import DocumentRole
from redaction_lab.fixtures import make_synthetic_pair

with TemporaryDirectory(prefix="redaction-lab-pdf-canary-") as directory:
    redacted, _ = make_synthetic_pair("two_boxes", Path(directory))
    result = ApplicationPdfWorker().process(
        redacted.read_bytes(), project_id="qualification-canary",
        role=DocumentRole.REDACTED,
    )
    if result.response.status is not WorkerStatus.PROCESSABLE:
        raise SystemExit("synthetic PDF canary did not produce PROCESSABLE")
PY
