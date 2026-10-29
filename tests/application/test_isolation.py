from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
import os
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
        self.closed = False

    def inspect(self, policy: RuntimePolicy) -> RuntimeInspection:
        return self.inspection

    def run(self, command: tuple[str, ...], *, input_bytes: bytes, timeout_seconds: int):
        self.command = command
        if self.timed_out:
            raise TimeoutError("deadline")
        return 0, self.response, b""

    def close(self) -> None:
        self.closed = True


def _policy() -> RuntimePolicy:
    return RuntimePolicy(
        executable="/opt/redaction-lab/bin/podman",
        executable_sha256="sha256:" + "a" * 64,
        executable_version="6.1.4",
        machine_name="redaction-lab-pdf-v1",
        image_digest="sha256:" + "1" * 64,
        runtime_root="/opt/redaction-lab/runtime/pdf-worker",
        containers_conf="/opt/redaction-lab/runtime/pdf-worker/containers.conf",
    )


def _inspection(**changes: object) -> RuntimeInspection:
    value = RuntimeInspection(
        executable_available=True, machine_name="redaction-lab-pdf-v1",
        rootless=True, machine_volumes=(), image_digest="sha256:" + "1" * 64,
        executable_sha256="sha256:" + "a" * 64,
        executable_version="6.1.4",
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


def test_unverified_runtime_lock_cannot_create_policy(tmp_path: Path) -> None:
    lock = tmp_path / "runtime.lock"
    lock.write_text(json.dumps({"runtime_verified": False}))

    with pytest.raises(RuntimeUnavailable, match="unverified"):
        RuntimePolicy.from_lock(lock, application_root=tmp_path)


def test_runtime_lock_resolves_only_exact_application_owned_paths(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime/pdf-worker"
    executable = runtime / "podman/bin/podman"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"synthetic podman")
    executable.chmod(0o700)
    (runtime / "state").mkdir()
    (runtime / "containers.conf").write_text("[machine]\nvolumes=[]\n")
    payload = {
        "runtime_verified": True,
        "protocol_version": WORKER_PROTOCOL_VERSION,
        "podman_executable": "runtime/pdf-worker/podman/bin/podman",
        "podman_executable_sha256": "sha256:" + sha256(executable.read_bytes()).hexdigest(),
        "podman_version": "6.1.4",
        "runtime_state": "runtime/pdf-worker/state",
        "containers_conf": "runtime/pdf-worker/containers.conf",
        "machine_name": "redaction-lab-pdf-v1",
        "machine_image_digest": "sha256:" + "2" * 64,
        "base_image_digest": "sha256:" + "3" * 64,
        "image_digest": "sha256:" + "4" * 64,
        "timeout_seconds": 60,
    }
    lock = tmp_path / "runtime.lock"
    lock.write_text(json.dumps(payload))

    policy = RuntimePolicy.from_lock(lock, application_root=tmp_path)

    assert policy.executable == str(executable)
    assert policy.runtime_root == str(runtime)
    assert policy.containers_conf == str(runtime / "containers.conf")
    for replacement in (
        "/tmp/podman",
        "runtime/pdf-worker/../podman",
        "runtime/other/podman",
    ):
        payload["podman_executable"] = replacement
        lock.write_text(json.dumps(payload))
        with pytest.raises(RuntimeUnavailable):
            RuntimePolicy.from_lock(lock, application_root=tmp_path)
    payload["podman_executable"] = "runtime/pdf-worker/podman/bin/podman"
    for key, replacement in (
        ("machine_name", "other-machine"),
        ("timeout_seconds", 0),
        ("image_digest", "sha256:not-a-digest"),
    ):
        original = payload[key]
        payload[key] = replacement
        lock.write_text(json.dumps(payload))
        with pytest.raises(RuntimeUnavailable):
            RuntimePolicy.from_lock(lock, application_root=tmp_path)
        payload[key] = original


def test_real_runner_binds_executable_version_environment_and_machine_policy(
    tmp_path: Path,
) -> None:
    runtime = tmp_path / "runtime"
    executable = runtime / "podman/bin/podman"
    executable.parent.mkdir(parents=True)
    state = runtime / "state"
    machine_config = state / "config/containers/podman/machine/applehv"
    machine_config.mkdir(parents=True)
    identity = state / "data/containers/podman/machine/machine"
    (machine_config / "redaction-lab-pdf-v1.json").write_text(
        json.dumps({
            "Name": "redaction-lab-pdf-v1",
            "Mounts": [],
            "HostUser": {"Rootful": False, "UID": 501},
            "SSH": {
                "IdentityPath": str(identity),
                "Port": 60660,
                "RemoteUsername": "core",
            },
        })
    )
    identity.parent.mkdir(parents=True)
    identity.write_text("synthetic-private-key")
    identity.chmod(0o600)
    (state / "tmp").mkdir()
    connection_file = state / "config/containers/podman-connections.json"
    connection_file.write_text(json.dumps({
        "Connection": {
            "Default": "redaction-lab-pdf-v1",
            "Connections": {
                "redaction-lab-pdf-v1": {
                    "URI": "ssh://core@127.0.0.1:60660/run/user/501/podman/podman.sock",
                    "Identity": str(identity),
                    "IsMachine": True,
                }
            },
        },
        "Farm": {},
    }))
    conf = runtime / "containers.conf"
    conf.write_text(
        f'[engine]\nhelper_binaries_dir=["{runtime}/podman/bin"]\n'
        '[machine]\nvolumes=[]\n'
        '[containers]\nnetns="none"\nread_only=true\nno_hosts=true\n'
    )
    executable.write_text(
        "#!/bin/sh\n"
        f"test \"$XDG_CONFIG_HOME\" = \"{state}/config\" || exit 41\n"
        f"test \"$XDG_DATA_HOME\" = \"{state}/data\" || exit 42\n"
        f"test \"$XDG_RUNTIME_DIR\" = \"{state}/tmp\" || exit 43\n"
        f"test \"$CONTAINERS_CONF\" = \"{conf}\" || exit 44\n"
        "if test \"$1\" = --version; then echo 'podman version 6.1.4'; exit 0; fi\n"
        "if test \"$1\" = machine; then printf '%s' '[{\"Name\":\"redaction-lab-pdf-v1\",\"Rootful\":false,\"State\":\"running\"}]'; exit 0; fi\n"
        "if test \"$3\" = info; then printf '%s' '{\"host\":{\"security\":{\"rootless\":true}}}'; exit 0; fi\n"
        "printf '%s' '[{\"Id\":\"1111111111111111111111111111111111111111111111111111111111111111\",\"RepoDigests\":[]}]'\n"
    )
    executable.chmod(0o700)
    policy = RuntimePolicy(
        executable=str(executable),
        executable_sha256="sha256:" + sha256(executable.read_bytes()).hexdigest(),
        executable_version="6.1.4",
        machine_name="redaction-lab-pdf-v1",
        image_digest="sha256:" + "1" * 64,
        runtime_root=str(runtime),
        containers_conf=str(conf),
    )
    inspection = SubprocessPodmanRunner().inspect(policy)

    assert inspection.executable_available is True
    assert inspection.machine_name == "redaction-lab-pdf-v1"
    assert inspection.rootless is True
    assert inspection.machine_volumes == ()
    assert inspection.image_digest == "sha256:" + "1" * 64
    assert inspection.executable_sha256 == policy.executable_sha256
    assert inspection.executable_version == "6.1.4"

    connection = json.loads(connection_file.read_text())
    connection["Connection"]["Connections"]["redaction-lab-pdf-v1"]["URI"] = (
        "ssh://root@127.0.0.1:60660/run/podman/podman.sock"
    )
    connection_file.write_text(json.dumps(connection))
    with pytest.raises(RuntimeUnavailable, match="connection"):
        SubprocessPodmanRunner().inspect(policy)
    connection["Connection"]["Connections"]["redaction-lab-pdf-v1"]["URI"] = (
        "ssh://core@127.0.0.1:60660/run/user/501/podman/podman.sock"
    )
    connection_file.write_text(json.dumps(connection))

    conf.write_text('[machine]\nvolumes=["/Users:/Users"]\n')
    with pytest.raises(RuntimeUnavailable, match="configuration"):
        SubprocessPodmanRunner().inspect(policy)


def test_real_runner_rejects_path_replacement_during_version_attestation(
    tmp_path: Path, monkeypatch
) -> None:
    executable = tmp_path / "podman"
    executable.write_bytes(b"trusted")
    executable.chmod(0o700)
    conf = tmp_path / "containers.conf"
    conf.write_text(
        f'[engine]\nhelper_binaries_dir=["{tmp_path}/podman/bin"]\n'
        '[machine]\nvolumes=[]\n'
        '[containers]\nnetns="none"\nread_only=true\nno_hosts=true\n'
    )
    (tmp_path / "state/config").mkdir(parents=True)
    (tmp_path / "state/data").mkdir()
    (tmp_path / "state/tmp").mkdir()
    policy = RuntimePolicy(
        executable=str(executable),
        executable_sha256="sha256:" + sha256(executable.read_bytes()).hexdigest(),
        executable_version="6.1.4",
        machine_name="redaction-lab-pdf-v1",
        image_digest="sha256:" + "1" * 64,
        runtime_root=str(tmp_path),
        containers_conf=str(conf),
    )

    def replace_path(*args, **kwargs):
        executable.rename(tmp_path / "original")
        executable.write_bytes(b"replacement")
        executable.chmod(0o700)
        return type("Completed", (), {"stdout": b"podman version 6.1.4\n"})()

    monkeypatch.setattr("redaction_lab.application.isolation.subprocess.run", replace_path)
    with pytest.raises(RuntimeUnavailable, match="changed"):
        SubprocessPodmanRunner().inspect(policy)


def test_runtime_path_audit_rejects_symlinked_final_directory(tmp_path: Path) -> None:
    runtime = tmp_path / "runtime"
    real_bin = tmp_path / "outside-bin"
    (runtime / "podman").mkdir(parents=True)
    real_bin.mkdir()
    (runtime / "podman/bin").symlink_to(real_bin, target_is_directory=True)

    with pytest.raises(RuntimeUnavailable, match="untrusted"):
        SubprocessPodmanRunner._audit_runtime_path(
            runtime, runtime / "podman/bin"
        )


def test_availability_probe_releases_runner_attestation() -> None:
    runner = FakeRunner(_inspection())
    probe = NonAuthoritativePdfWorkerProbe(_policy(), runner)

    probe.ensure_available()

    assert runner.closed is True


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
        "--interactive", "--network=none", "--read-only", "--cap-drop=all",
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


def test_subprocess_runner_bounds_stdout_before_returning(tmp_path: Path) -> None:
    executable = tmp_path / "podman"
    executable.write_text("#!/bin/sh\nhead -c 4096 /dev/zero | tr '\\000' x\n")
    executable.chmod(0o700)
    class TrackingRunner(SubprocessPodmanRunner):
        cleanup_had_environment = False

        def _terminate_container(self, command):
            self.cleanup_had_environment = self._environment is not None

    runner = TrackingRunner(max_stdout_bytes=64)
    runner._executable_fd = os.open(executable, os.O_RDONLY)  # type: ignore[attr-defined]
    runner._executable_identity = runner._file_identity(  # type: ignore[attr-defined]
        os.fstat(runner._executable_fd)  # type: ignore[attr-defined]
    )
    connection = tmp_path / "connection.json"
    connection.write_text("{}")
    runner._connection_fd = os.open(connection, os.O_RDONLY)  # type: ignore[attr-defined]
    runner._connection_identity = runner._file_identity(  # type: ignore[attr-defined]
        os.fstat(runner._connection_fd)  # type: ignore[attr-defined]
    )
    runner._connection_path = connection  # type: ignore[attr-defined]
    runner._environment = {  # type: ignore[attr-defined]
        "PATH": "/usr/bin:/bin",
        "XDG_CONFIG_HOME": str(tmp_path / "state/config"),
        "CONTAINERS_CONF": str(tmp_path / "containers.conf"),
    }

    with pytest.raises(RuntimeUnavailable, match="output limit"):
        runner.run(
            (str(executable), "--connection", "probe"),
            input_bytes=b"",
            timeout_seconds=5,
        )
    assert runner.cleanup_had_environment is True


def test_subprocess_runner_cleans_named_container_on_nonzero_exit(
    tmp_path: Path,
) -> None:
    executable = tmp_path / "podman"
    executable.write_text("#!/bin/sh\nexit 7\n")
    executable.chmod(0o700)

    class TrackingRunner(SubprocessPodmanRunner):
        cleanup_had_environment = False

        def _terminate_container(self, command):
            self.cleanup_had_environment = self._environment is not None

    runner = TrackingRunner()
    runner._executable_fd = os.open(executable, os.O_RDONLY)  # type: ignore[attr-defined]
    runner._executable_identity = runner._file_identity(  # type: ignore[attr-defined]
        os.fstat(runner._executable_fd)  # type: ignore[attr-defined]
    )
    connection = tmp_path / "connection.json"
    connection.write_text("{}")
    runner._connection_fd = os.open(connection, os.O_RDONLY)  # type: ignore[attr-defined]
    runner._connection_identity = runner._file_identity(  # type: ignore[attr-defined]
        os.fstat(runner._connection_fd)  # type: ignore[attr-defined]
    )
    runner._connection_path = connection  # type: ignore[attr-defined]
    runner._environment = {  # type: ignore[attr-defined]
        "PATH": "/usr/bin:/bin",
        "XDG_CONFIG_HOME": str(tmp_path / "state/config"),
        "CONTAINERS_CONF": str(tmp_path / "containers.conf"),
    }

    returncode, _, _ = runner.run(
        (str(executable), "--connection", "probe", "run", "--name", "failed"),
        input_bytes=b"",
        timeout_seconds=5,
    )

    assert returncode == 7
    assert runner.cleanup_had_environment is True
