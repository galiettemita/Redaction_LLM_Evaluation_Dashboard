"""Fail-closed launcher abstraction for the dedicated PDF worker runtime."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import secrets
import subprocess
from threading import Event, Thread
from typing import Protocol

from redaction_lab.application.config import WORKER_TIMEOUT_SECONDS
from redaction_lab.application.config import MAX_WORKER_RESPONSE_BYTES
from redaction_lab.application.worker_protocol import (
    WORKER_PROTOCOL_VERSION,
    WorkerRequest,
    WorkerResponse,
    decode_response,
    encode_request,
)
from redaction_lab.contracts import DocumentRole


class RuntimeUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class RuntimePolicy:
    executable: str
    machine_name: str
    image_digest: str
    timeout_seconds: int = WORKER_TIMEOUT_SECONDS

    @classmethod
    def from_lock(cls, lock_path: Path) -> "RuntimePolicy":
        payload = json.loads(Path(lock_path).read_text(encoding="utf-8"))
        digests = (
            payload.get("machine_image_digest"),
            payload.get("base_image_digest"),
            payload.get("image_digest"),
        )
        if (
            payload.get("runtime_verified") is not True
            or payload.get("protocol_version") != WORKER_PROTOCOL_VERSION
            or any(
                not isinstance(value, str)
                or not value.startswith("sha256:")
                or value == "sha256:" + "0" * 64
                for value in digests
            )
        ):
            raise RuntimeUnavailable("PDF worker runtime lock is unverified")
        return cls(
            executable=payload["podman_executable"],
            machine_name=payload["machine_name"],
            image_digest=payload["image_digest"],
            timeout_seconds=int(payload["timeout_seconds"]),
        )


@dataclass(frozen=True)
class RuntimeInspection:
    executable_available: bool
    machine_name: str
    rootless: bool
    machine_volumes: tuple[str, ...]
    image_digest: str


@dataclass(frozen=True)
class WorkerObservation:
    """Bound protocol output, not proof of production runtime authority."""

    response: WorkerResponse
    image_digest: str


class RuntimeRunner(Protocol):
    def inspect(self, policy: RuntimePolicy) -> RuntimeInspection: ...

    def run(
        self,
        command: tuple[str, ...],
        *,
        input_bytes: bytes,
        timeout_seconds: int,
    ) -> tuple[int, bytes, bytes]: ...


class SubprocessPodmanRunner:
    """Production runner. Tests inject a fake and never operate Podman."""

    def __init__(self, *, max_stdout_bytes: int = MAX_WORKER_RESPONSE_BYTES) -> None:
        self.max_stdout_bytes = max_stdout_bytes

    @staticmethod
    def _terminate_container(command: tuple[str, ...]) -> None:
        try:
            name = command[command.index("--name") + 1]
            prefix = command[:3]
            subprocess.run(
                (*prefix, "kill", "--signal=KILL", name),
                capture_output=True,
                timeout=5,
                check=False,
            )
            subprocess.run(
                (*prefix, "rm", "--force", name),
                capture_output=True,
                timeout=5,
                check=False,
            )
        except Exception:
            pass

    def inspect(self, policy: RuntimePolicy) -> RuntimeInspection:
        executable = Path(policy.executable)
        available = executable.is_file() and bool(executable.stat().st_mode & 0o111)
        if not available:
            return RuntimeInspection(False, policy.machine_name, False, (), "")
        try:
            machine = subprocess.run(
                (policy.executable, "machine", "inspect", policy.machine_name),
                check=True,
                capture_output=True,
                timeout=10,
            )
            image = subprocess.run(
                (policy.executable, "image", "inspect", policy.image_digest),
                check=True,
                capture_output=True,
                timeout=10,
            )
            machine_data = json.loads(machine.stdout)[0]
            image_data = json.loads(image.stdout)[0]
            volumes = tuple(machine_data.get("Host", {}).get("Volumes", ()))
            rootful = bool(machine_data.get("Rootful", False))
            digests = tuple(image_data.get("RepoDigests", ()))
            observed_digest = policy.image_digest if any(
                value.endswith(policy.image_digest) for value in digests
            ) else ""
            return RuntimeInspection(
                True, policy.machine_name, not rootful, volumes, observed_digest
            )
        except Exception:
            return RuntimeInspection(False, policy.machine_name, False, (), "")

    def run(
        self,
        command: tuple[str, ...],
        *,
        input_bytes: bytes,
        timeout_seconds: int,
    ) -> tuple[int, bytes, bytes]:
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdin is not None
        assert process.stdout is not None
        assert process.stderr is not None
        stdout = bytearray()
        stderr = bytearray()
        overflow = Event()

        def write_input() -> None:
            try:
                process.stdin.write(input_bytes)
                process.stdin.flush()
            except BrokenPipeError:
                pass
            finally:
                process.stdin.close()

        def read_bounded(stream, destination: bytearray, limit: int) -> None:
            while True:
                chunk = stream.read(65_536)
                if not chunk:
                    return
                remaining = limit + 1 - len(destination)
                if remaining > 0:
                    destination.extend(chunk[:remaining])
                if len(destination) > limit:
                    overflow.set()
                    process.kill()
                    return

        threads = (
            Thread(target=write_input, daemon=True),
            Thread(target=read_bounded, args=(process.stdout, stdout, self.max_stdout_bytes), daemon=True),
            Thread(target=read_bounded, args=(process.stderr, stderr, 4096), daemon=True),
        )
        for thread in threads:
            thread.start()
        try:
            returncode = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired as error:
            process.kill()
            process.wait()
            self._terminate_container(command)
            raise TimeoutError("isolated PDF worker deadline exceeded") from error
        finally:
            for thread in threads:
                thread.join(timeout=5)
        if overflow.is_set():
            self._terminate_container(command)
            raise RuntimeUnavailable("isolated PDF worker output limit exceeded")
        return returncode, bytes(stdout), bytes(stderr)


class _IsolatedPdfWorkerClient:
    def __init__(self, policy: RuntimePolicy, runner: RuntimeRunner | None = None) -> None:
        self.policy = policy
        self.runner = runner or SubprocessPodmanRunner()

    def _verify_runtime(self) -> RuntimeInspection:
        inspection = self.runner.inspect(self.policy)
        if (
            not inspection.executable_available
            or inspection.machine_name != self.policy.machine_name
            or not inspection.rootless
            or inspection.machine_volumes
            or inspection.image_digest != self.policy.image_digest
        ):
            raise RuntimeUnavailable("approved isolated PDF runtime is unavailable")
        return inspection

    def _command(self, nonce: str) -> tuple[str, ...]:
        return (
            self.policy.executable,
            "--connection",
            self.policy.machine_name,
            "run",
            "--rm",
            "--name",
            f"redaction-lab-pdf-{nonce}",
            "--pull=never",
            "--network=none",
            "--read-only",
            "--read-only-tmpfs=false",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,nodev,size=256m",
            "--cap-drop=all",
            "--security-opt=no-new-privileges",
            "--user=65532:65532",
            "--pids-limit=32",
            "--memory=1536m",
            "--memory-swap=1536m",
            "--cpus=1",
            "--shm-size=32m",
            "--ulimit=nofile=64:64",
            "--log-driver=none",
            self.policy.image_digest,
        )

    def process(
        self,
        pdf_bytes: bytes,
        *,
        project_id: str,
        role: DocumentRole,
    ) -> WorkerObservation:
        inspection = self._verify_runtime()
        nonce = secrets.token_hex(16)
        request = WorkerRequest(
            protocol_version=WORKER_PROTOCOL_VERSION,
            request_nonce=nonce,
            project_id=project_id,
            role=role,
            input_sha256=sha256(pdf_bytes).hexdigest(),
            byte_count=len(pdf_bytes),
        )
        try:
            returncode, stdout, _stderr = self.runner.run(
                self._command(nonce),
                input_bytes=encode_request(request, pdf_bytes),
                timeout_seconds=self.policy.timeout_seconds,
            )
        except TimeoutError as error:
            raise RuntimeUnavailable("isolated PDF worker timeout") from error
        if returncode != 0:
            raise RuntimeUnavailable("isolated PDF worker failed")
        response = decode_response(stdout)
        if (
            response.protocol_version != request.protocol_version
            or response.request_nonce != request.request_nonce
            or response.project_id != request.project_id
            or response.role is not request.role
            or response.input_sha256 != request.input_sha256
        ):
            raise ValueError("isolated worker response binding mismatch")
        return WorkerObservation(response=response, image_digest=inspection.image_digest)


class NonAuthoritativePdfWorkerProbe(_IsolatedPdfWorkerClient):
    """Injectable protocol/command probe with no persistence authority.

    This seam exists only for deterministic tests. Application processing never
    accepts an instance of this class or any caller-provided runner or policy.
    """


_INSTALL_RUNTIME_LOCK = (
    Path(__file__).resolve().parents[3] / "packaging" / "pdf-worker" / "runtime.lock"
)


class ApplicationPdfWorker(_IsolatedPdfWorkerClient):
    """Application-owned production worker composed from install-owned state."""

    def __init__(self) -> None:
        policy = RuntimePolicy.from_lock(_INSTALL_RUNTIME_LOCK)
        super().__init__(policy, SubprocessPodmanRunner())

    def ensure_available(self) -> None:
        """Verify the concrete runtime before a durable job may be claimed."""

        self._verify_runtime()
