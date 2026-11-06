#!/bin/sh
# Synthetic-only v2 protocol and container-isolation qualification.
set -eu
umask 077
script_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
python_executable=${REDACTION_LAB_PYTHON:-"$script_root/.venv/bin/python"}
exec "$python_executable" -I -B - "$script_root" <<'PY'
from dataclasses import replace
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
import secrets
import shutil
import sys

root = Path(sys.argv[1])
sys.path.insert(0, str(root / 'src'))
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader
import pypdfium2 as pdfium
from redaction_lab.application.inference_runtime import InferenceRuntime
from redaction_lab.application.isolation import RuntimePolicy, SubprocessPodmanRunner, NonAuthoritativePdfWorkerProbe, ApplicationPdfWorker
from redaction_lab.application.worker_protocol import WorkerStatus, WORKER_PROTOCOL_VERSION, MAX_HEADER_BYTES
from redaction_lab.application.config import MAX_CANONICAL_TEXT_BYTES
from redaction_lab.contracts import DocumentRole

lock = InferenceRuntime._read_lock(root / 'packaging/pdf-worker/runtime.lock')
assert lock['protocol_version'] == WORKER_PROTOCOL_VERSION
runtime = InferenceRuntime._resolve_locked_path('runtime/pdf-worker')
assert shutil.disk_usage(runtime).free >= 8 * 1024**3
policy = RuntimePolicy(str(runtime / 'podman/bin/podman'), lock['podman_executable_sha256'],
    lock['podman_version'], lock['machine_name'], lock['image_digest'], str(runtime), str(runtime / 'containers.conf'))

def pdf(redacted):
    data = BytesIO()
    canvas = Canvas(data, pagesize=(612, 792), invariant=1)
    canvas.setFont('Helvetica', 11)
    prefix, answer, suffix = 'The capital of France is ', 'Paris', ' and it is known for the Eiffel Tower.'
    canvas.drawString(72, 700, prefix + answer + suffix)
    if redacted:
        canvas.rect(72 + stringWidth(prefix, 'Helvetica', 11) - 1, 697,
                    stringWidth(answer, 'Helvetica', 11) + 2, 14, fill=1, stroke=0)
    canvas.save()
    return data.getvalue()

def scanned_pdf(redacted):
    image = pdfium.PdfDocument(pdf(redacted))[0].render(scale=200/72).to_pil()
    data = BytesIO()
    canvas = Canvas(data, pagesize=(612, 792), invariant=1)
    canvas.drawImage(ImageReader(image), 0, 0, width=612, height=792)
    canvas.save()
    return data.getvalue()

receipts = {}
for role in (DocumentRole.REDACTED, DocumentRole.REFERENCE):
    worker = NonAuthoritativePdfWorkerProbe(policy, SubprocessPodmanRunner())
    result = worker.process(pdf(role is DocumentRole.REDACTED), project_id='v2-qualification', role=role)
    response = result.response
    assert response.status is WorkerStatus.PROCESSABLE
    assert response.protocol_version == 'pdf-worker-v2'
    if role is DocumentRole.REFERENCE:
        assert response.reference_text and 'Paris' in response.reference_text
        assert response.reference_hash == sha256(response.reference_text.encode()).hexdigest()
        assert len(response.reference_text.encode()) <= MAX_CANONICAL_TEXT_BYTES
        assert response.canonical_text is None and response.targets == ()
    else:
        assert len(response.targets) == 1 and 'Paris' not in response.canonical_text
        assert response.reference_text is None
    receipts[role.value] = {'input_sha256': response.input_sha256, 'status': response.status.value,
        'canonical_hash': response.canonical_hash, 'reference_hash': response.reference_hash}

scan_receipts = {}
for role in (DocumentRole.REDACTED, DocumentRole.REFERENCE):
    response = NonAuthoritativePdfWorkerProbe(policy, SubprocessPodmanRunner()).process(
        scanned_pdf(role is DocumentRole.REDACTED), project_id='v3-raster-qualification', role=role).response
    assert response.status is WorkerStatus.PROCESSABLE
    if role is DocumentRole.REDACTED:
        assert len(response.targets) == 1
        assert response.targets[0].analysis_method.value == 'raster-ocr-near-black-text-occlusion'
        assert response.detector_version == 'raster-dark-text-v1'
        assert response.canonicalizer_version == 'ocr-visible-text-v1'
        assert 'Paris' not in response.canonical_text
        assert response.reference_text is None
    else:
        assert response.reference_canonicalizer_version == 'ocr-reference-text-v1'
        assert response.reference_text and 'Paris' in response.reference_text
        assert response.canonical_text is None and not response.targets
    scan_receipts[role.value] = {'input_sha256': response.input_sha256,
        'status': response.status.value, 'canonical_hash': response.canonical_hash,
        'reference_hash': response.reference_hash}

covered = NonAuthoritativePdfWorkerProbe(policy, SubprocessPodmanRunner()).process(
    pdf(True), project_id='v2-covered-reference', role=DocumentRole.REFERENCE).response
assert covered.reference_text is not None and 'Paris' not in covered.reference_text
oversize = BytesIO()
pages = Canvas(oversize, invariant=1)
for _ in range(101):
    pages.drawString(72, 700, 'Synthetic page limit probe')
    pages.showPage()
pages.save()
bounded = NonAuthoritativePdfWorkerProbe(policy, SubprocessPodmanRunner()).process(
    oversize.getvalue(), project_id='v2-page-limit', role=DocumentRole.REFERENCE).response
assert bounded.status is WorkerStatus.UNSUPPORTED and bounded.reference_text is None

runner = SubprocessPodmanRunner()
client = NonAuthoritativePdfWorkerProbe(policy, runner)
client._verify_runtime()
nonce = secrets.token_hex(16)
command = list(client._command(nonce))
probe = """
import os,json,socket,resource
from io import BytesIO
from pathlib import Path
status=Path('/proc/self/status').read_text()
assert os.getuid()==65532
assert 'CapEff:\\t0000000000000000' in status
assert 'NoNewPrivs:\\t1' in status
assert not Path('/Users').exists() and not Path('/app/artifacts').exists()
try:
 Path('/app/untrusted-write').write_text('x')
 raise AssertionError('writable root')
except OSError:pass
sock=socket.socket();sock.settimeout(1)
try:
 sock.connect(('1.1.1.1',443))
 raise AssertionError('network enabled')
except OSError:pass
finally:sock.close()
assert Path('/sys/fs/cgroup/memory.max').read_text().strip()=='1610612736'
assert Path('/sys/fs/cgroup/pids.max').read_text().strip()=='32'
assert resource.getrlimit(resource.RLIMIT_NOFILE)==(64,64)
assert Path('/sys/fs/cgroup/cpu.max').read_text().split()[0]!='max'
from redaction_lab.experimental_scoring import score_text_agreement
from redaction_lab.ocr import TesseractOcrEngine
from reportlab.pdfgen.canvas import Canvas
import pypdfium2 as pdfium
ocr_pdf=BytesIO();ocr_canvas=Canvas(ocr_pdf,pagesize=(612,792),invariant=1)
ocr_canvas.setFont('Helvetica',20);ocr_canvas.drawString(72,700,'Visible OCR qualification text')
ocr_canvas.save()
ocr_page=pdfium.PdfDocument(ocr_pdf.getvalue())[0]
ocr_words=TesseractOcrEngine().recognize(ocr_page.render(scale=200/72).to_pil()).words
assert any(word.text.casefold()=='visible' and word.confidence>=60 for word in ocr_words)
for reference in ('Temperature was - 5 degrees.', 'Temperature was − 5 degrees.'):
 evidence=score_text_agreement(reference, 'Temperature was + 5 degrees.')
 assert evidence.experimental_score==60.0 and evidence.applied_caps==(60.0,)
 assert not evidence.subscores.normalized_exact_match and evidence.verified_score is None
print(json.dumps({'isolation':'PASS','ocr_runtime':'PASS'}))
"""
try:
    # Same runtime flags, replace only the executable entrypoint for the canary.
    command[-1:-1] = ['--entrypoint', 'python']
    code, output, _ = runner.run(tuple(command) + ('-c', probe), input_bytes=b'', timeout_seconds=15)
    assert code == 0, 'isolated policy probe failed'
    probe_result = json.loads(output)
    assert probe_result['isolation'] == 'PASS'
    assert probe_result['ocr_runtime'] == 'PASS'
    # Oversized framing is rejected with bounded output, and --rm cleans failure.
    client._verify_runtime()
    code, output, _ = runner.run(client._command(secrets.token_hex(16)),
        input_bytes=b'x' * (MAX_HEADER_BYTES + 1) + b'\n', timeout_seconds=15)
    assert code != 0 and len(output) < 65536
    client._verify_runtime()
    code, output, _ = runner.run(tuple(command) + ('-c', 'raise SystemExit(7)'), input_bytes=b'', timeout_seconds=15)
    assert code == 7
    client._verify_runtime()
    try:
        runner.run(tuple(command) + ('-c', 'import time; time.sleep(10)'), input_bytes=b'', timeout_seconds=1)
        raise AssertionError('deadline did not stop container')
    except TimeoutError:
        pass
    client._verify_runtime()
    result = runner._run_verified(policy, (policy.executable, '--connection', policy.machine_name,
        'ps', '--all', '--filter', 'name=redaction-lab-pdf-', '--format', '{{.Names}}'))
    assert result.stdout.strip() == b'', 'qualification container was not cleaned'
finally:
    runner.close()
assert shutil.disk_usage(runtime).free >= 8 * 1024**3
if lock['runtime_verified']:
    ApplicationPdfWorker().ensure_available()
print(json.dumps({'protocol_version': WORKER_PROTOCOL_VERSION, 'image_digest': policy.image_digest,
    'reference_v2_protocol': 'PASS', 'redacted_source_excludes_covered_text': 'PASS',
    'reference_text_bounds': 'PASS', 'adversarial_isolation': 'PASS', 'signed_quantity_regression': 'PASS', 'failure_cleanup': 'PASS',
    'timeout_cleanup': 'PASS', 'covered_reference_excluded': 'PASS', 'reference_page_limit': 'PASS',
    'ocr_runtime': 'PASS', 'raster_redacted_reference': 'PASS',
    'receipts': receipts, 'scan_receipts': scan_receipts}, sort_keys=True))
PY
