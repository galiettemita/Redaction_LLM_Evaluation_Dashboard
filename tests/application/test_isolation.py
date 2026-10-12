from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from redaction_lab.application.isolation import (
    ApplicationPdfWorker,
    NonAuthoritativePdfWorkerProbe,
    RuntimeInspection,
    RuntimePolicy,
    RuntimeUnavailable,
    SubprocessPodmanRunner,
)
from redaction_lab.application.worker_protocol import WORKER_PROTOCOL_VERSION
from redaction_lab.contracts import DocumentRole


class FakeRunner:
    def __init__(self, inspection: RuntimeInspection, response: bytes = b"", *, timed_out: bool = False):
        self.inspection = inspection
        self.response = response
        self.timed_out = timed_out
        self.command: tuple[str, ...] | None = None

    def inspect(self, policy: RuntimePolicy) -> RuntimeInspection:
        return self.inspection

    def run(self, command: tuple[str, ...], *, input_bytes: bytes, timeout_seconds: int):
        self.command = command
        if self.timed_out:
            raise TimeoutError("deadline")
        return 0, self.response, b""


def _policy() -> RuntimePolicy:
    return RuntimePolicy(
        executable="/opt/redaction-lab/bin/podman",
        machine_name="redaction-lab-pdf-v1",
        image_digest="sha256:" + "1" * 64,
    )


def _inspection(**changes: object) -> RuntimeInspection:
    value = RuntimeInspection(
        executable_available=True, machine_name="redaction-lab-pdf-v1",
        rootless=True, machine_volumes=(), image_digest="sha256:" + "1" * 64,
    )
    return replace(value, **changes)


def _response(pdf: bytes, nonce: str) -> bytes:
    payload = {
        "protocol_version": WORKER_PROTOCOL_VERSION,
        "request_nonce": nonce,
        "project_id": "project",
        "role": "REFERENCE",
        "input_sha256": sha256(pdf).hexdigest(),
        "status": "PROCESSABLE",
        "page_count": 1,
        "detector_version": None,
        "canonicalizer_version": None,
        "canonical_text": None,
        "canonical_hash": None,
        "targets": [],
        "reason_code": None,
    }
    return json.dumps(payload).encode()


def test_runtime_absence_or_host_volume_share_fails_closed() -> None:
    pdf = b"%PDF-reference"
    for inspection in (
        _inspection(executable_available=False),
        _inspection(machine_volumes=("/Users:/Users",)),
        _inspection(image_digest="sha256:" + "2" * 64),
        _inspection(rootless=False),
    ):
        with pytest.raises(RuntimeUnavailable):
            NonAuthoritativePdfWorkerProbe(_policy(), FakeRunner(inspection)).process(
                pdf, project_id="project", role=DocumentRole.REFERENCE,
            )


def test_shipped_unverified_runtime_lock_cannot_create_policy() -> None:
    lock = Path(__file__).resolve().parents[2] / "packaging/pdf-worker/runtime.lock"

    with pytest.raises(RuntimeUnavailable, match="unverified"):
        RuntimePolicy.from_lock(lock)


def test_application_worker_accepts_no_caller_policy_or_runner() -> None:
    with pytest.raises(TypeError):
        ApplicationPdfWorker(_policy())  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        ApplicationPdfWorker(runner=FakeRunner(_inspection()))  # type: ignore[call-arg]


def test_verified_runtime_uses_hardened_container_command(monkeypatch) -> None:
    pdf = b"%PDF-reference"
    nonce = "a" * 32
    monkeypatch.setattr("redaction_lab.application.isolation.secrets.token_hex", lambda _: nonce)
    runner = FakeRunner(_inspection(), _response(pdf, nonce))

    result = NonAuthoritativePdfWorkerProbe(_policy(), runner).process(
        pdf, project_id="project", role=DocumentRole.REFERENCE,
    )

    assert result.image_digest == _policy().image_digest
    command = runner.command
    assert command is not None
    for required in (
        "--network=none", "--read-only", "--cap-drop=all",
        "--security-opt=no-new-privileges", "--pids-limit=32",
        "--memory=1536m", "--memory-swap=1536m", "--cpus=1", "--pull=never",
    ):
        assert required in command
    assert "--name" in command
    assert command[command.index("--name") + 1] == f"redaction-lab-pdf-{nonce}"
    assert not any("/Users" in argument or "volume" in argument for argument in command)


def test_nonce_hash_project_role_version_and_timeout_are_fail_closed(monkeypatch) -> None:
    pdf = b"%PDF-reference"
    nonce = "a" * 32
    monkeypatch.setattr("redaction_lab.application.isolation.secrets.token_hex", lambda _: nonce)
    for field, value in (
        ("request_nonce", "b" * 32), ("input_sha256", "c" * 64),
        ("project_id", "other"), ("role", "REDACTED"),
        ("protocol_version", "old-protocol"),
    ):
        payload = json.loads(_response(pdf, nonce))
        payload[field] = value
        with pytest.raises(ValueError, match="binding|worker response"):
            NonAuthoritativePdfWorkerProbe(_policy(), FakeRunner(_inspection(), json.dumps(payload).encode())).process(
                pdf, project_id="project", role=DocumentRole.REFERENCE,
            )
    with pytest.raises(RuntimeUnavailable, match="timeout"):
        NonAuthoritativePdfWorkerProbe(_policy(), FakeRunner(_inspection(), timed_out=True)).process(
            pdf, project_id="project", role=DocumentRole.REFERENCE,
        )


def test_subprocess_runner_bounds_stdout_before_returning() -> None:
    runner = SubprocessPodmanRunner(max_stdout_bytes=64)

    with pytest.raises(RuntimeUnavailable, match="output limit"):
        runner.run(
            ("/usr/bin/python3", "-c", "import sys; sys.stdout.write('x' * 4096)"),
            input_bytes=b"",
            timeout_seconds=5,
        )
