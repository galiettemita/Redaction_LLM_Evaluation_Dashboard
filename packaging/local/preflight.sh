#!/bin/sh
# Read-only validation. This script never installs prerequisites or invokes Podman.
set -eu
if [ "$#" -ne 0 ]; then
    printf '%s\n' 'Usage: preflight.sh (configuration uses REDACTION_LAB_* environment variables)' >&2
    exit 2
fi
package_dir=$(CDPATH= cd -P -- "$(dirname -- "$0")" && pwd -P)
python_executable=${REDACTION_LAB_PYTHON:-python3}
if ! command -v "$python_executable" >/dev/null 2>&1; then
    printf '%s\n' '{"error":{"code":"PYTHON_MISSING","message":"Select an existing Python interpreter with REDACTION_LAB_PYTHON; nothing was installed"}}'
    exit 1
fi
exec "$python_executable" -I -B - "$package_dir" <<'PY'
import hashlib
import importlib.metadata
import runpy
import json
import os
from pathlib import Path
import platform
import stat
import sys


def fail(code, message):
    print(json.dumps({"error": {"code": code, "message": message}}))
    raise SystemExit(1)


try:
    local = Path(sys.argv[1])
    root = local.parents[1]
    # This helper uses only stdlib. Avoid importing application dependencies
    # until their platform/interpreter/installed-version checks have passed.
    static = runpy.run_path(str(root / "src/redaction_lab/api/static.py"))
    manifest = static["read_local_manifest"](root)
    host = os.environ.get("REDACTION_LAB_HOST", "127.0.0.1")
    if host != "127.0.0.1" or manifest["host"] != "127.0.0.1":
        fail("INVALID_HOST", "Host must be exactly 127.0.0.1")
    raw_port = os.environ.get("REDACTION_LAB_PORT", str(manifest["default_port"]))
    if (not raw_port.isascii() or not raw_port.isdecimal()
            or len(raw_port) > 5 or not 1 <= int(raw_port) <= 65535):
        fail("INVALID_PORT", "Port must be a decimal integer between 1 and 65535")
    supported = manifest["supported_platform"]
    if platform.system() != supported["system"] or platform.machine() != supported["machine"]:
        fail("UNSUPPORTED_PLATFORM", "This candidate supports macOS Apple Silicon (arm64) only")
    if platform.python_version() != manifest["python_version"]:
        fail("PYTHON_PIN_MISMATCH", "Existing Python must match version " + manifest["python_version"])
    for name, expected in manifest["dependency_pins"].items():
        try:
            installed = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            fail("DEPENDENCY_MISSING", "Missing prerequisite: " + name + "==" + expected)
        if installed != expected:
            fail("DEPENDENCY_PIN_MISMATCH", "Prerequisite must match " + name + "==" + expected)
    worker = manifest["pdf_worker"]
    lock_bytes = (root / worker["lock_path"]).read_bytes()
    if hashlib.sha256(lock_bytes).hexdigest() != worker["lock_sha256"]:
        fail("RUNTIME_LOCK_MISMATCH", "Worker lock changed; a separately reviewed package is required")
    lock = json.loads(lock_bytes)
    if lock.get("runtime_verified") is not False or worker["runtime_qualified"] is not False:
        fail("RUNTIME_NOT_AUTHORIZED", "This candidate permits only the unqualified API demo")
    sys.path.insert(0, str(root / "src"))
    from redaction_lab.application.paths import resolve_paths, preflight_directories
    from redaction_lab.api.app import create_app
    frontend = static["create_static_app"](None, root, manifest.get("frontend"))
    try:
        paths = resolve_paths()
        if (paths.root == Path.home() or paths.root in Path.home().parents
                or paths.root == root or root in paths.root.parents or paths.root in root.parents):
            raise ValueError("data home is not a dedicated directory outside the checkout")
        preflight_directories((paths.root, paths.artifacts, paths.temporary, paths.logs, paths.backups))
        if paths.root.exists() and stat.S_IMODE(paths.root.stat().st_mode) != 0o700:
            raise ValueError("existing data home is not private")
    except (OSError, ValueError):
        fail("UNSAFE_DATA_HOME", "Choose a dedicated private absolute data directory outside the checkout, without symlinks")
    print(json.dumps({
        "api_version": "0.1", "state": "DEGRADED", "runtime_qualified": False,
        "mode": "local", "host": host, "port": int(raw_port),
        "frontend_available": frontend.frontend_available, "recipient_acceptance": "NOT_RUN",
        "message": "API prerequisites match; frontend availability requires a verified bundle; PDF processing and inference remain unavailable",
    }, sort_keys=True))
except (OSError, ValueError, KeyError, TypeError, ImportError):
    fail("PACKAGE_INVALID", "Package files or imports are unavailable; nothing was installed")
PY
