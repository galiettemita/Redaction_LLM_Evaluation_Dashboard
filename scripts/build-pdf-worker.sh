#!/bin/sh
# Offline rebuild only. Does not start a machine or download any artifact.
set -eu
umask 077
script_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python_executable=${REDACTION_LAB_PYTHON:-"$script_root/.venv/bin/python"}
exec "$python_executable" -I -B - "$script_root" <<'PY'
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import time

root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'src'))
from redaction_lab.application.inference_runtime import InferenceRuntime
from redaction_lab.application.isolation import RuntimePolicy, SubprocessPodmanRunner

source_image = 'sha256:7a78eaf7ef812d354f0abe13f40c6c0a4e3684d94f72002245c5249249bf293b'
lock = InferenceRuntime._read_lock(root / 'packaging/pdf-worker/runtime.lock')
runtime = InferenceRuntime._resolve_locked_path('runtime/pdf-worker')
policy = RuntimePolicy(str(runtime / 'podman/bin/podman'), lock['podman_executable_sha256'],
    lock['podman_version'], lock['machine_name'], source_image, str(runtime), str(runtime / 'containers.conf'))
runner = SubprocessPodmanRunner()
process = None
reserve = 8 * 1024**3
minimum_free = shutil.disk_usage(runtime).free
if minimum_free - 512 * 1024**2 < reserve:
    raise SystemExit('Insufficient reserve for the bounded offline rebuild')
try:
    inspection = runner.inspect(policy)
    if (not inspection.rootless or inspection.machine_volumes or inspection.image_digest != source_image
            or not inspection.executable_available):
        raise SystemExit('Exact installed dependency image and isolated running machine required')
    with tempfile.TemporaryDirectory(prefix='redaction-lab-v2-build-') as directory:
        context = Path(directory)
        (context / 'src').mkdir()
        for path in sorted((root / 'src').rglob('*')):
            if '__pycache__' in path.parts:
                continue
            if path.is_symlink():
                raise SystemExit('Symlink in source build context')
            if path.is_file():
                destination = context / path.relative_to(root)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, destination)
        shutil.copyfile(root / 'packaging/pdf-worker/Containerfile', context / 'Containerfile')
        command = [policy.executable, '--connection', policy.machine_name, 'build',
            '--pull=never', '--network=none', '--tag', 'localhost/redaction-lab/pdf-worker:v2',
            '--file', str(context / 'Containerfile'), str(context)]
        runner._assert_executable_identity(policy, 'before build')
        process = subprocess.Popen(command, env=runner._environment)
        deadline = time.monotonic() + 300
        while process.poll() is None:
            minimum_free = min(minimum_free, shutil.disk_usage(runtime).free)
            if minimum_free < reserve or time.monotonic() > deadline:
                process.terminate()
                raise SystemExit('Build stopped: disk reserve or deadline gate')
            time.sleep(0.25)
        runner._assert_executable_identity(policy, 'after build')
        if process.returncode:
            raise SystemExit(process.returncode)
        print(json.dumps({'build_minimum_free_bytes': minimum_free, 'source_image': source_image}))
finally:
    if process is not None and process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    runner.close()
PY
