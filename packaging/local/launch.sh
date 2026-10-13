#!/bin/sh
# Code-only API demo. No downloads, model calls, Podman or static-file server.
set -eu
umask 077
package_dir=$(CDPATH= cd -P -- "$(dirname -- "$0")" && pwd -P)
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--check" ]; }; then
    printf '%s\n' 'Usage: launch.sh [--check]' >&2
    exit 2
fi
if [ "$#" -eq 1 ]; then
    exec /bin/sh "$package_dir/preflight.sh"
fi
/bin/sh "$package_dir/preflight.sh"
python_executable=${REDACTION_LAB_PYTHON:-python3}
exec "$python_executable" -I -B - "$package_dir" <<'PY'
import json
import os
from pathlib import Path
import signal
import sys
from wsgiref.simple_server import WSGIRequestHandler, WSGIServer, make_server

root = Path(sys.argv[1]).parents[1]
sys.path.insert(0, str(root / "src"))
from redaction_lab.api.app import create_app
from redaction_lab.application.application_store import ApplicationStore
from redaction_lab.application.artifact_store import ArtifactStore
from redaction_lab.application.paths import initialize_paths, resolve_paths
from redaction_lab.application.upload_service import UploadService


class QuietHandler(WSGIRequestHandler):
    def log_message(self, format, *args):
        # Do not retain document identifiers, URLs, raw requests or bodies.
        pass


class LocalServer(WSGIServer):
    def get_request(self):
        connection, address = super().get_request()
        connection.settimeout(10)
        return connection, address

    def handle_error(self, request, client_address):
        print("REQUEST_FAILED: local request could not be completed", file=sys.stderr)


def stop(signum, frame):
    raise KeyboardInterrupt


server = None
artifacts = None
try:
    manifest = json.loads((root / "packaging/local/manifest.json").read_text())
    # Bind before creating directories or migrating the dedicated application DB.
    port = int(os.environ.get("REDACTION_LAB_PORT", str(manifest["default_port"])))
    server = make_server("127.0.0.1", port, None, server_class=LocalServer, handler_class=QuietHandler)
    paths = initialize_paths(resolve_paths())
    store = ApplicationStore(paths.database, backup_directory=paths.backups)
    artifacts = ArtifactStore(paths.artifacts, paths.temporary)
    server.set_app(create_app(UploadService(artifacts, store)))
    signal.signal(signal.SIGTERM, stop)
    print(f"API diagnostic: http://127.0.0.1:{port}/api/v1/health", flush=True)
    print("DEGRADED: frontend, PDF processing, inference and recipient acceptance are unavailable", flush=True)
    server.serve_forever()
except KeyboardInterrupt:
    pass
except Exception:
    print("STARTUP_FAILED: local API could not start; check preflight, port availability and dedicated data directory", file=sys.stderr)
    raise SystemExit(1)
finally:
    if server is not None:
        server.server_close()
    if artifacts is not None:
        artifacts.close()
PY
