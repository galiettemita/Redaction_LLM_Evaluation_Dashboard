# Isolated PDF worker packaging

This directory specifies the proposed macOS Apple Silicon PDF-worker image and
Podman policy. It is intentionally fail-closed: `runtime.lock` contains
unverified zero digests until the separately authorized packaging and clean-Mac
qualification task records exact Podman, VM, base-image and built-image digests.

Task 7A tests the protocol and command construction with mocks only. It does not
install Podman, create a VM, pull or build an image, or claim that isolation has
been verified on this computer.

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

The eventual packaging task must replace every zero digest, provide a complete
offline dependency/image archive, generate an SBOM and license inventory, set
`runtime_verified` to true only after clean-device adversarial checks, and record
the supported Podman/macOS versions.
