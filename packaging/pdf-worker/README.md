# Isolated PDF worker packaging

This directory specifies the qualified macOS Apple Silicon PDF-worker image and
Podman policy. Task RL-RUNTIME-009A qualified the exact lock on macOS 26.5.1,
Apple arm64, Podman client 6.1.4, and Podman Machine OS 6.1.3. The lock binds the
application-owned Podman executable, machine source, base image, built image,
protocol and deadline by immutable identity.

This is host-specific engineering qualification, not institutional data
permission, public deployment approval, scientific validation, or proof that a
different computer has the same runtime state.

`requirements.lock` is generated from the frozen project lock and requires hash
verification. The image build is deliberately offline: acquire every arm64
musllinux wheel listed in `integrity-manifest.json` into
`packaging/pdf-worker/wheelhouse/` and verify its size and SHA-256 before running
`scripts/build-pdf-worker.sh`. The wheel binaries are qualification inputs and
are intentionally not committed. The container build also enforces the hashes
in `requirements.lock` with `--no-index --require-hashes`.

Those injectable mocks are explicitly non-authoritative probes: they cannot be
supplied to the application document worker and cannot persist Task 4 sources or
mark document jobs ready. Production composition reads only the install-owned
`runtime.lock`, creates the concrete Podman runner internally, verifies it before
claiming a job, and then keeps runtime invocation, response binding, deterministic
source reconstruction and persistence in one application-owned path.

The qualified runtime must use a dedicated rootless machine with `volumes = []`.
Each disposable container receives one PDF through stdin, has no network,
mounts, database, artifacts, credentials or reference side channel, and returns
one bounded JSON response through stdout. The host verifies runtime policy,
request bindings and deterministic Task 4 identities. It does not independently
prove the semantic correctness of PDF parsing.

The portable Podman payload and all state live beneath
`~/Library/Application Support/RedactionLab/runtime/pdf-worker/` (or the same
relative directory beneath `REDACTION_LAB_HOME`). The runtime uses dedicated
XDG config/data/runtime directories and `containers.conf`; it does not install
the privileged Podman helper or use default user Podman state.

`qualification-sources.json` records official sources, signatures, versions,
licenses, vulnerability observations, exact image identities and canary results.
`integrity-manifest.json` records acquired byte identities.
`sbom.cdx.json` records the observed Alpine and Python contents of the exact
qualified worker image.

The qualification sequence is:

1. Verify and place the official Podman payload and Podman Machine OS image in
   the application runtime root using the identities in the manifests.
2. Initialize `redaction-lab-pdf-v1` as an AppleHV, rootless machine with
   `volumes = []`, 2 CPUs, 2048 MiB memory, 512 MiB swap and a 10 GiB disk.
3. Pull only the exact base manifest from `runtime.lock`.
4. Populate and verify the local wheelhouse, then run
   `scripts/build-pdf-worker.sh`; the build itself has no network and cannot pull.
5. Compare the resulting image ID with `runtime.lock`, start the dedicated
   machine, and run `scripts/verify-pdf-worker.sh`.

Application startup and every worker request re-attest the exact Podman bytes
and version, retained-file identity, application-owned environment, live
rootless machine, empty machine mounts and exact worker image. Each disposable
container receives one synthetic or authorized PDF only through stdin with
`--interactive`; it has no network or host mounts, a read-only root, dropped
capabilities, no-new-privileges, non-root UID and bounded resources/output/time.
