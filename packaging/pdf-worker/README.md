# Isolated PDF worker packaging

This directory specifies the qualified macOS Apple Silicon PDF-worker image and
Podman policy. Task RL-RUNTIME-009A qualified the exact lock on macOS 26.5.1,
Apple arm64, Podman client 6.1.4, and Podman Machine OS 6.1.3. The lock binds the
application-owned Podman executable, machine source, base image, built image,
protocol and deadline by immutable identity.

This is host-specific engineering qualification, not institutional data
permission, public deployment approval, scientific validation, or proof that a
different computer has the same runtime state.

The current v2 refresh reuses already installed, hash-bound dependencies without
network access; see the exact offline recipe below. `requirements.lock` and the
wheel entries in `integrity-manifest.json` retain the original acquisition
provenance. No current script acquires wheels or installs new dependencies.

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
`~/Library/Application Support/RedactionLab/runtime/pdf-worker/`, or the literal
`pdf-worker` child of an explicit trusted `REDACTION_LAB_RUNTIME_ROOT`. Without an
explicit runtime root, legacy resolution beneath `REDACTION_LAB_HOME` remains
fail-closed. The runtime uses dedicated
XDG config/data/runtime directories and `containers.conf`; it does not install
the privileged Podman helper or use default user Podman state.

`qualification-sources.json` records official sources, signatures, versions,
licenses, vulnerability observations, exact image identities and canary results.
`integrity-manifest.json` records acquired byte identities.
`sbom.cdx.json` records the observed Alpine and Python contents of the exact
qualified worker image.

The original RL-RUNTIME-009A acquisition initialized the dedicated machine,
obtained the pinned base and verified wheelhouse, and independently qualified
v1. Those historical acquisition steps are not part of the current v2 refresh.
Do not treat them as permission to acquire or initialize another runtime.

Application startup and every worker request re-attest the exact Podman bytes
and version, retained-file identity, application-owned environment, live
rootless machine, empty machine mounts and exact worker image. Each disposable
container receives one synthetic or authorized PDF only through stdin with
`--interactive`; it has no network or host mounts, a read-only root, dropped
capabilities, no-new-privileges, non-root UID and bounded resources/output/time.

## pdf-worker-v2 source refresh (2026-11-05)

The current lock pins a newly built v2 image, independently qualified for
isolated redacted and reference extraction. The immutable prior v1 image is
used **only as an offline dependency stage**, because its original wheelhouse is
no longer present. `Containerfile` retains the exact original Python base and
copies the observed `/usr/local` dependency bytes, then replaces application
source with explicit 0555 read-only permissions for the non-root worker.
The v1 operational qualification is not inherited.

`scripts/build-pdf-worker.sh` accepts the existing interpreter through
`REDACTION_LAB_PYTHON` and the trusted installed runtime through
`REDACTION_LAB_RUNTIME_ROOT`. It requires the exact dependency image and a
running isolated machine, creates a small source-only context, excludes caches
and unrelated files, and builds with `--pull=never --network=none`. It reserves
8 GiB free disk plus 512 MiB projected build headroom, monitors the reserve during
the bounded build, and deletes only its temporary context. It never starts a VM
or downloads dependencies. New acquisition still requires its separate gate.

`scripts/verify-pdf-worker.sh` exercises genuine synthetic redacted/reference
framed protocol, exact visible reference hashes, covered-text exclusion, page
and framing bounds, non-root/no-network/read-only/no-capabilities/no-new-privileges
and resource controls, nonzero failure cleanup and deadline cleanup. It uses a
non-authoritative qualification probe until the observed lock is marked verified;
that probe never persists application sources. Afterwards the production
`ApplicationPdfWorker` independently attests the exact lock and runtime.

The integrity manifest binds all 38 source files in the built image. Complete
3,216-entry dependency file/link inventories and 21 license file hashes were
observed in both exact images and match. The 55-component CycloneDX SBOM was
reconciled against the new image's observed Python and APK versions/licenses.
Original download and advisory observations retain their original audit date;
source refresh is not a new advisory scan. Exact new image/protocol identities,
source hash, disk measurements and synthetic canaries are in the records here.

A separate synthetic workspace can reuse the trusted runtime root. The PDF and
model resolvers share the same absolute owner-controlled root checks, and the
PDF runner still verifies executable identity, configuration, retained connection
state, live rootless/no-share machine and exact image on every operation.
