# RL-MVP-007D Gate A feasibility report

Task: RL-MVP-007D-QUALIFICATION-01 — portable application qualification  
Role: QA / Security  
Gate: **A — read-only feasibility only**  
Live inspection baseline: `62124fa47b093e5e9a5383c1fd5ba5d055736da9` / E0064  
Controlling packet: `docs/project/task_packets/RL-MVP-007D-QUALIFICATION-01.md`

## Gate A verdict

**GATE_A_COMPLETE — Gate B is NOT execution-ready and remains BLOCKED pending explicit owner authorization plus missing integrity/license/runtime-build evidence.**

This Gate A report completes the authorized read-only inventory, security-boundary inspection, clean-recipient requirement assessment, acceptance-gap register and proposed Gate B plan. It does **not** qualify the PDF runtime, approve installation, authorize any download/container operation, establish final Task 7D acceptance or establish scientific D03–D06 validity.

No tests, software installation, downloads, containers, VMs, PDF processing, migrations, inference, provider calls or paid operations were executed during Gate A.

## Evidence inspected

Pinned to live main `62124fa47b093e5e9a5383c1fd5ba5d055736da9` unless stated otherwise:

- `AGENTS.md`
- `docs/project/CURRENT_STATE.md` — E0064
- `docs/project/DECISIONS.md` — E0064 Gate A authorization
- `docs/project/AGENT_HANDOFF.md`
- `docs/project/MASTER_SPEC.md`
- `docs/project/AGENT_OPERATING_GUIDE.md`
- `docs/project/task_packets/RL-MVP-007D-QUALIFICATION-01.md`
- `docs/project/API_CONTRACT_V0_1.md`
- `packaging/pdf-worker/runtime.lock`
- `packaging/pdf-worker/Containerfile`
- `packaging/pdf-worker/containers.conf`
- `packaging/pdf-worker/README.md`
- `scripts/build-pdf-worker.sh`
- `scripts/verify-pdf-worker.sh`
- `packaging/local/manifest.json`
- `packaging/local/preflight.sh`
- `packaging/local/launch.sh`
- `packaging/local/README.md`
- `pyproject.toml`
- `uv.lock`
- `web/package-lock.json`
- `src/redaction_lab/application/isolation.py`
- `src/redaction_lab/application/worker_protocol.py`
- `src/redaction_lab/application/config.py`
- `src/redaction_lab/application/paths.py`
- `src/redaction_lab/application/artifact_store.py`
- `src/redaction_lab/application/migration.py`
- `src/redaction_lab/application/document_worker.py`
- `src/redaction_lab/store.py`
- relevant test definitions under `tests/application/`, `tests/security/test_pdf_worker_container.py`, and `tests/packaging/`.

## 1. PDF-runtime inventory

### Current lock state

`packaging/pdf-worker/runtime.lock` currently records:

| Field | Current value | Gate A assessment |
| --- | --- | --- |
| schema | 1 | Present |
| worker protocol | `pdf-worker-v1` | Present and matched by code |
| Podman executable | `/opt/redaction-lab/bin/podman` | Path specified; binary/version not present or verified by Gate A |
| Podman version | `UNVERIFIED` | **BLOCKER** |
| machine name | `redaction-lab-pdf-v1` | Specified only |
| machine image digest | all-zero SHA-256 | **BLOCKER** |
| base image digest | all-zero SHA-256 | **BLOCKER** |
| worker image digest | all-zero SHA-256 | **BLOCKER** |
| Python | 3.12.14 | Intended pin |
| worker timeout | 60 seconds | Matches Task-7A limit |
| `runtime_verified` | false | Correct fail-closed current state |

`RuntimePolicy.from_lock` refuses policy creation unless `runtime_verified:true`, the protocol matches, and all three digests are nonzero SHA-256 values. The shipped state therefore correctly prevents production worker authority.

### Container recipe

`packaging/pdf-worker/Containerfile` currently:

- uses `python:3.12-slim@sha256:<all-zero>` as a placeholder base;
- copies only `src/` into the image;
- runs as UID/GID 65532;
- enters `python -m redaction_lab.application.worker_protocol`;
- does **not** install the Python packages imported by the worker.

The worker imports at least `pydantic`, `pypdf`, and through detector/canonicalization code `pdfplumber` plus their transitives. A stock `python:3.12-slim` image is not evidenced to contain those packages.

**Blocking build gap:** the current Containerfile is not sufficient evidence of a runnable worker image even after replacing the zero base digest.

### Build/verification scripts

`scripts/build-pdf-worker.sh` refuses to build unless `runtime.lock` already contains `"runtime_verified": true`, then invokes `podman build --pull=never --network=none`.

`scripts/verify-pdf-worker.sh` also refuses unless the lock is already verified and, even then, prints a canary instruction and exits 2.

This creates an intentional fail-closed state but also a **qualification bootstrap gap**: the repository has no executable path that builds an unverified candidate image, verifies it, and only then writes trusted runtime digests.

Gate B therefore requires an explicitly authorized qualification workflow amendment; simply installing Podman is insufficient.

## 2. Application dependency inventory

### Local application prerequisite pins

`packaging/local/manifest.json` requires macOS Darwin/arm64, CPython 3.12.14 and these exact installed distributions:

| Distribution | Version |
| --- | --- |
| pdfplumber | 0.11.10 |
| pdfminer.six | 20260107 |
| pypdf | 6.20.0 |
| pypdfium2 | 5.14.0 |
| pydantic | 2.14.0 |
| pydantic-core | 2.50.0 |
| annotated-types | 0.8.0 |
| typing-extensions | 4.16.0 |
| typing-inspection | 0.4.4 |
| reportlab | 4.5.1 |
| Pillow | 12.3.0 |
| charset-normalizer | 3.5.2 |
| cryptography | 50.0.2 |
| cffi | 2.1.1 |
| pycparser | 3.11 |

`uv.lock` contains exact artifacts and SHA-256 hashes for the Python dependency graph, including macOS arm64 wheels where published. It also contains test-only packages; it is broader than the local runtime manifest.

### Frontend build dependencies

The committed frontend bundle is already prebuilt, so Node is not required to *run* the local website. `web/package-lock.json` nevertheless records exact integrity metadata and license fields for the build graph, including React 19.2.0, React DOM 19.2.0, TypeScript 5.9.3, Vite 7.3.5 and the approved esbuild 0.27.2 override.

### Missing offline prerequisite bundle

The repository explicitly states that no wheel archive, Python installer, fully offline prerequisite bundle or clean-recipient installer is supplied.

**Clean-recipient blocker:** the current launcher works only when the recipient already has an exactly compatible Python and all pinned distributions. There is no approved reproducible acquisition/install mechanism.

## 3. Integrity and license evidence

### Integrity evidence present

- Python distributions in `uv.lock`: registry URLs plus SHA-256 hashes.
- Frontend build graph in `web/package-lock.json`: exact resolved npm registry URLs and integrity hashes.
- Static frontend artifacts: manifest SHA-256, sizes and MIME types.
- PDF worker runtime lock: schema and digest fields exist, but runtime/base/machine/image values are still zero placeholders.
- Local package pins the SHA-256 of the current **unverified** worker lock.

### Integrity evidence missing / unverified

1. **Podman binary:** no approved version, download URL, package digest/signature, notarization evidence or executable digest is recorded.
2. **Podman machine image:** no nonzero immutable digest or acquisition provenance.
3. **Base container image:** zero placeholder digest; no verified source/signature evidence.
4. **Built worker image:** zero placeholder digest; no SBOM, image manifest/archive digest or signature.
5. **Offline Python environment:** no archived wheelhouse/interpreter package with a package-level manifest and aggregate digest.
6. **Recipient package:** no signed/notarized release artifact or aggregate package digest is defined.

### License evidence present

- The npm lock records package license metadata for the frontend dependency graph.
- The project documents acknowledge that scientific/model/runtime licensing remains unqualified.

### License evidence missing

No repository SBOM, license inventory or NOTICE-style artifact was found for:
- Podman;
- Podman machine/base OS image;
- Python base image;
- worker image contents;
- the Python runtime dependency set as a release unit.

`uv.lock` records artifact integrity but does not itself provide license fields. The local README explicitly says an SBOM/license inventory is not supplied.

**Gate B stop condition:** no runtime qualification should be declared until these license and integrity records are obtained from trusted upstream metadata and archived in an owner-approved evidence artifact.

## 4. PDF-worker isolation and security boundaries

### Host/runtime qualification boundary

Production `ApplicationPdfWorker` is application-owned. It reads only the install-owned runtime lock and creates the concrete `SubprocessPodmanRunner`; callers cannot inject an authoritative worker/policy/runner.

`DocumentWorker.run_once` calls `ensure_available()` **before** durable job claim. With the current unverified lock, document processing therefore remains ACCEPTED/unclaimed and cannot create a Task-4 source.

### Runtime inspection

Before processing, the host verifies:
- executable exists and is executable;
- expected machine name;
- rootless machine;
- no machine host volumes;
- exact expected image digest in Podman inspection output.

### Per-container command

The reviewed command requests:
- exact locked image with `--pull=never`;
- `--network=none`;
- `--read-only`;
- disposable tmpfs only at `/tmp`, noexec/nosuid/nodev, 256 MiB;
- no capabilities;
- no-new-privileges;
- nonroot UID/GID 65532;
- pids 32;
- memory/swap 1536 MiB;
- one CPU;
- shm 32 MiB;
- nofile 64;
- logging disabled;
- no host artifact/database/reference mount.

`containers.conf` separately declares no machine volumes, no network namespace and read-only containers.

### Protocol boundary

The host streams one PDF through stdin using a length-prefixed strict JSON header plus raw bytes.

Request/response binding covers:
- protocol;
- nonce;
- project;
- document role;
- input SHA-256;
- byte count.

Output is bounded; stderr is bounded; timeout kills the process/container.

Reference-role processing may validate that a PDF is parseable/page-bounded but cannot return canonical text or targets. Redacted material can return only validated bounded canonical text/geometry under the strict response schema.

### Arbitrary host reparsing

The application processing path feeds verified artifact bytes to the isolated worker. The host converts returned material into a deterministic prediction source without invoking a second arbitrary-PDF parser in the application worker path.

The worker itself uses strict `pypdf` plus detector/canonicalization logic inside isolation.

### Residual isolation gaps requiring Gate B evidence

Inspection of command construction is not runtime proof. Gate B must empirically establish on the clean recipient:
- Podman machine is actually rootless;
- no host shares/volumes exist;
- container network is actually unavailable;
- no unexpected inherited environment/secrets;
- read-only root and tmpfs behavior are enforced;
- resource limits are effective;
- container cannot access host artifacts/database/home;
- timeout/kill/removal works;
- exact image digest remains pinned throughout execution.

## 5. Data, filesystem and persistence boundaries

### Artifact confinement

Artifact storage uses:
- content-addressed SHA-256 logical keys;
- descriptor-relative directory traversal;
- `O_NOFOLLOW`;
- no-clobber hard-link publication;
- read-time digest verification;
- bounded temporary recovery.

Published prior tests exist for root/prefix/leaf symlinks and replacement races. They were **not executed in Gate A**.

### Application paths

Managed paths require absolute non-root locations, no parent traversal, no symlink components and current-user ownership. Directories are mode 0700.

### SQLite migration/recovery

Migration code uses:
- persistent database-specific `flock`;
- no-follow database/backup descriptors;
- subprocess helper with only four passed FDs;
- isolated child cwd rather than parent cwd mutation;
- verified pre-migration backup;
- integrity check;
- cleanup of validated incomplete backup files only;
- migration checksum binding.

Previously published tests cover WAL, hot rollback journal, simultaneous independent startup, parent death, live `.part` backup protection and evidence preservation. These tests were **not executed in Gate A**.

### Persistence expectations

The local application retains uploaded artifacts, database/evidence and backups across restart. No general deletion API exists.

Clean-recipient acceptance must therefore allocate a dedicated private application directory and define teardown/cleanup separately; deleting the package directory alone is not equivalent to deleting retained state.

## 6. Network / API boundary

The local launcher is hard-bound to literal `127.0.0.1`.

The API rejects non-loopback REMOTE_ADDR, unsafe Host/Origin and incompatible request framing. The static host rejects duplicate singleton HTTP headers and Transfer-Encoding before WSGI normalization.

No worker runtime egress is permitted by policy. No external model/provider path is connected for Task 7D qualification.

Gate B should capture actual listening sockets and worker network canaries rather than relying only on source inspection.

## 7. Portable clean-recipient requirements

### Explicit supported target

Current packaging supports:
- **macOS on Apple Silicon / arm64 only**;
- native CPython **3.12.14**;
- exact pinned Python distributions in the local manifest;
- literal loopback service;
- dedicated private application data directory;
- exact reviewed frontend asset bundle.

Unsupported under the current package:
- Intel macOS / Rosetta;
- Linux;
- Windows;
- other Python versions;
- recipients lacking the exact prerequisites.

### Hardware requirements evidenced by repository

Per-worker container limits specify:
- 1 CPU;
- 1536 MiB memory/swap;
- 256 MiB tmpfs;
- 32 MiB shm.

The repository does **not** specify:
- minimum host RAM;
- minimum free disk;
- minimum macOS release;
- minimum Apple Silicon generation;
- Podman machine CPU/memory/disk allocation.

Those must be measured/selected before a clean-recipient claim.

### Required clean-recipient setup artifacts not yet present

- exact Podman version/install provenance;
- compatible Podman machine creation configuration;
- offline or otherwise controlled Python 3.12.14 acquisition;
- exact dependency wheelhouse/archive;
- SBOM/license inventory;
- worker image archive or deterministic build inputs;
- nonzero runtime/base/machine/image digests;
- clean uninstall/cleanup procedure;
- second-device execution evidence.

### Documentation drift

The current `packaging/local/manifest.json` has a verified frontend inventory and `frontend_available:true`, while portions of `packaging/local/README.md` still describe a null frontend inventory / blocked Vite build.

This is not a runtime-security bypass, but it is a **recipient usability/qualification blocker**: Gate B/final acceptance must use corrected, reviewable recipient instructions before claiming independent setup success.

## 8. Mapped test evidence

### Repository tests that exist

Gate A inspected test definitions for:

- runtime absence/volume-share fail-closed;
- shipped unverified runtime lock rejection;
- no caller policy/runner injection;
- hardened container command;
- nonce/hash/project/role/version/timeout fail-closed;
- bounded worker stdout;
- unverified runtime leaves job ACCEPTED and Task-4 unchanged;
- artifact symlink/race/tamper/recovery protections;
- migration backup/integrity, WAL/hot journal, helper FD isolation, timeout, interprocess serialization and lock inheritance;
- loopback package preflight, runtime-lock mismatch, restart persistence and frontend verification;
- static Host/Origin/framing/symlink/traversal/tamper defenses.

### Previously reported evidence

Prior Backend/Packaging and independent QA handoffs reported successful mock/synthetic software suites on exact reviewed candidates before integration. Those reports establish review history, **not current Gate A execution**.

### NOT RUN in Gate A

The following were deliberately not executed:

- any pytest/Node/shell tests;
- local launcher/preflight;
- Podman version/inspect/machine commands;
- container build/run/inspect;
- image pull/load/save;
- synthetic or real PDF processing;
- network isolation canaries;
- filesystem escape canaries;
- timeout/resource-limit canaries;
- migration/restart tests;
- browser tests;
- clean recipient setup;
- dependency installation/download;
- package/license scanners;
- vulnerability scanners;
- model/provider calls;
- inference;
- deployment;
- private data handling.

## 9. Gate A blockers / risk register

| ID | Severity | Gate-B impact |
| --- | --- | --- |
| GA-01 | Blocking | Runtime lock has unverified Podman and zero machine/base/worker digests. |
| GA-02 | Blocking | Containerfile base digest is zero placeholder. |
| GA-03 | Blocking | Worker Containerfile does not install its required Python dependencies; no worker-specific locked dependency assembly exists. |
| GA-04 | Blocking | Build script requires `runtime_verified:true` before building, and verification script always exits 2; no executable qualification bootstrap exists. |
| GA-05 | Blocking | No SBOM/license inventory for Podman/base image/worker image/Python runtime dependency release set. |
| GA-06 | Blocking | No trusted Podman binary provenance/version/signature/digest is recorded. |
| GA-07 | Blocking for clean-recipient claim | No offline prerequisite bundle/interpreter/wheelhouse or clean second-device evidence. |
| GA-08 | Blocking for recipient acceptance | Local README contains stale frontend-availability instructions inconsistent with the current manifest. |
| GA-09 | Residual | Host hardware/macOS/Podman-machine minimums are unspecified. |
| GA-10 | Residual | Runtime security properties have only source/mock evidence; no clean-device network/mount/resource escape canaries have been executed. |
| GA-11 | Residual | No signed/notarized aggregate recipient package/release integrity mechanism is defined. |
| GA-12 | Scientific boundary | D03–D06 remain unapproved; runtime qualification cannot convert UNKNOWN truth/null scores into scientific validation. |

No observed Gate A issue requires weakening current fail-closed behavior. The application is safer remaining unqualified until these blockers are resolved.

## 10. Proposed Gate B execution plan — NOT AUTHORIZED

### Required owner permissions before any command

A Gate B packet must explicitly authorize:

1. One named clean compatible second Mac: Darwin/arm64, separate from the development Mac.
2. Zero-cost downloads of exact approved:
   - Podman release/install package;
   - Python 3.12.14 installer/environment artifact;
   - pinned Python wheels from the exact `uv.lock`;
   - exact base container image by nonzero digest.
3. Verification of upstream signatures/checksums/licenses and creation of a public-safe SBOM/license record.
4. Podman installation and creation/start/stop/removal of one dedicated rootless machine.
5. Image pull/load/build/save/inspect operations with network permitted **only during explicitly listed acquisition steps**; worker execution itself remains `--network=none`.
6. Synthetic-only PDF fixture processing from repository-approved fixtures.
7. Temporary qualification directories and final cleanup.
8. Narrow packaging changes necessary to remove current bootstrap blockers, proposed scope:
   - `packaging/pdf-worker/Containerfile`
   - `packaging/pdf-worker/runtime.lock`
   - `scripts/build-pdf-worker.sh`
   - `scripts/verify-pdf-worker.sh`
   - one approved worker dependency-lock/build-input artifact if required
   - recipient qualification documentation/evidence files explicitly named by the Gate B packet.
9. Separate independent exact-SHA review before any merge.
10. **No model inference, provider/API call, private data, scientific scoring or deployment.**

If the owner does not authorize the packaging changes in item 8, Gate B is **BLOCKED** because the current worker image cannot be reproducibly qualified from repository state.

### Gate B Phase 0 — immutable values recorded before execution

Before downloads, the Gate B packet must freeze:

- `PODMAN_VERSION=<exact version>`
- `PODMAN_DOWNLOAD_URL=<official URL>`
- `PODMAN_SHA256=<trusted upstream digest>`
- `BASE_IMAGE_REF=python:3.12-slim@sha256:<nonzero exact digest>`
- exact macOS version range;
- exact Podman machine CPU/memory/disk settings;
- exact wheel filenames/hashes selected from `uv.lock`;
- approved licenses for Podman, Python/base image and every redistributed dependency;
- expected worker image tag and protocol `pdf-worker-v1`;
- a fixed synthetic fixture list.

No variable may be filled ad hoc during execution.

### Gate B Phase 1 — clean-recipient host inventory

Proposed commands on the approved clean Mac, captured to a private/local qualification log with no user documents:

```sh
sw_vers
uname -m
uname -a
system_profiler SPHardwareDataType
df -h
sysctl -n hw.memsize
shasum -a 256 <approved-downloaded-artifacts>
```

Success:
- Darwin/arm64 exactly;
- macOS/hardware within the newly approved bounds;
- all downloaded bytes match approved hashes.

Failure: stop; do not install.

### Gate B Phase 2 — package/license integrity

Using only owner-approved local artifacts, proposed checks:

```sh
python3.12 --version
python3.12 -m pip --version
uv lock --check --offline
python3.12 -m pip check
npm --prefix web audit --package-lock-only --ignore-scripts --audit-level=low
```

Additionally generate/verify the approved SBOM/license inventory for:
- Python runtime dependencies;
- Podman;
- base image OS packages;
- worker image contents.

Success: no unknown/unapproved dependency, no hash mismatch, no unresolved license blocker, no prohibited install hook during qualification assembly.

Failure: stop and return to Lead.

### Gate B Phase 3 — Podman installation and rootless machine

Only after Phase 1/2 evidence passes:

```sh
<approved installer command for the exact hashed Podman artifact>
/opt/redaction-lab/bin/podman --version
/opt/redaction-lab/bin/podman machine init --cpus <PIN> --memory <PIN> --disk-size <PIN> redaction-lab-pdf-v1
/opt/redaction-lab/bin/podman machine start redaction-lab-pdf-v1
/opt/redaction-lab/bin/podman machine inspect redaction-lab-pdf-v1
```

The exact installer command must be written in the Gate B packet after Podman distribution choice is approved; Gate A does not select a download channel.

Success:
- exact approved Podman version;
- rootless;
- volumes empty;
- machine configuration exactly pinned.

Failure: remove/stop machine and stop qualification.

### Gate B Phase 4 — base image and worker build

After authorized packaging correction removes the zero-digest/dependency/bootstrap gaps:

```sh
/opt/redaction-lab/bin/podman --connection redaction-lab-pdf-v1 pull <exact-base-image-by-digest>
/opt/redaction-lab/bin/podman --connection redaction-lab-pdf-v1 image inspect <exact-base-image-by-digest>
sh scripts/build-pdf-worker.sh
/opt/redaction-lab/bin/podman --connection redaction-lab-pdf-v1 image inspect <built-worker-image>
```

Build must install only the approved hash-pinned worker dependencies from an authorized source/offline wheelhouse, use the exact nonzero base digest, and produce an immutable worker digest.

Record:
- base image digest;
- worker image digest;
- image configuration;
- package/SBOM output;
- no unexpected layer/content.

Do **not** set `runtime_verified:true` yet.

### Gate B Phase 5 — isolation canaries before application authority

Run synthetic no-secret canaries against the exact image:

- rootless identity;
- no host mounts;
- no network/DNS/loopback egress from worker container;
- read-only root;
- only bounded `/tmp` writable;
- no inherited credentials/environment;
- no access to host home, repository, application artifacts or SQLite path;
- cap-drop/no-new-privileges;
- pids/memory/CPU/shm/nofile limits;
- stdout/stderr bounds;
- 60-second timeout/kill/removal behavior;
- `--pull=never` prevents surprise acquisition.

Example inspection commands to be frozen in the Gate B packet:

```sh
/opt/redaction-lab/bin/podman --connection redaction-lab-pdf-v1 inspect <container-or-image>
/opt/redaction-lab/bin/podman --connection redaction-lab-pdf-v1 image inspect <worker-digest>
/opt/redaction-lab/bin/podman --connection redaction-lab-pdf-v1 machine inspect redaction-lab-pdf-v1
```

Security success requires observed state to match every source-declared isolation property. Any network/host-volume/privilege mismatch is an immediate STOP.

### Gate B Phase 6 — synthetic PDF functional qualification

Use only named repository synthetic PDF fixtures authorized in the Gate B packet.

Required cases:

1. valid redacted synthetic PDF with supported text target;
2. reference PDF: processability only, no canonical/target material;
3. no-redaction PDF;
4. malformed PDF;
5. encrypted PDF;
6. over-page-limit PDF;
7. oversized request rejected before worker;
8. worker malformed/oversized response;
9. worker timeout;
10. restart after accepted/terminal state.

For each case verify:
- request byte hash / nonce / project / role binding;
- no reference content enters prediction material;
- unsupported/failed cases return no targets/canonical material;
- unverified state cannot create Task-4 source;
- once the exact runtime is separately marked qualified, only redacted PROCESSABLE response can create a bound source;
- no model prediction/inference is enqueued by document processing;
- no score becomes non-null.

### Gate B Phase 7 — host application security regression

Execute the existing repository suites on the clean Mac using the exact candidate revision:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src <approved-python> -B -m pytest -q -p no:cacheprovider tests/application tests/security tests/packaging
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src <approved-python> -B -m pytest -q -p no:cacheprovider
```

Also exercise:
- artifact symlink/prefix replacement cases;
- migration WAL/hot journal/two-process lock cases;
- loopback Host/Origin/framing cases;
- website static tamper cases;
- runtime-unverified 503 before qualification;
- qualified worker success after qualification.

Success requires zero unexpected failures and byte-equivalent Task-4/Task-6 evidence across restart/migration checks.

### Gate B Phase 8 — clean-recipient setup acceptance

Starting from a second clean compatible Mac and only the approved recipient bundle/instructions:

1. verify package aggregate digest/signature;
2. install/select exact prerequisites using the authorized procedure;
3. run read-only preflight;
4. launch on literal 127.0.0.1;
5. verify reviewed frontend and health;
6. synthetic upload with and without optional reference;
7. verify UNKNOWN truth and null scores;
8. process through the qualified isolated PDF worker;
9. stop/restart; confirm IDs/artifacts/job state persist without new prediction attempt;
10. confirm backup/recovery behavior;
11. confirm no external listener/network egress;
12. follow documented cleanup and verify no process/container/machine remains when cleanup is requested.

No private or real research PDF is permitted.

### Gate B success criteria

Gate B may report **software/runtime qualification PASS** only when:

- all runtime/base/machine/worker digests are nonzero and independently observed;
- Podman/version/install integrity and licenses are recorded;
- worker dependency installation is reproducible and hash-pinned;
- SBOM/license inventory has no unresolved blocker;
- all isolation canaries pass;
- synthetic functional cases pass;
- current regression suites pass on the clean device;
- recipient setup succeeds from the documented procedure;
- restart/persistence/migration behavior is correct;
- reference isolation/UNKNOWN truth/null scores remain intact;
- no unexpected network/host path access occurs;
- no paid operation or inference occurs.

Scientific D03–D06 approval remains separate even after a software PASS.

### Gate B failure / rollback

On any integrity, license, isolation, provenance or unexpected-network failure:

1. stop the application;
2. stop/remove worker containers;
3. stop/remove the dedicated Podman machine if cleanup is authorized;
4. retain only public-safe diagnostics/digests required for the handoff;
5. do not mark `runtime_verified:true`;
6. do not merge qualification changes;
7. report the exact failure to Lead.

If a worker image has been built but not qualified, it remains non-authoritative and must not be referenced by a verified runtime lock.

### Gate B cost expectation

Proposed Gate B is **zero paid-service cost** but may require software downloads and local compute/storage. Any paid license, subscription, cloud resource or vendor API immediately stops execution pending separate owner approval.

## 11. Gate A conclusion

Gate A establishes that the application's existing software boundaries are designed to fail closed and that the repository contains substantial mock/synthetic security coverage. It also establishes that the **actual PDF runtime is intentionally absent/unverified and is not presently reproducible from the repository without additional packaging work**.

The highest-priority Gate B prerequisites are:

1. approve exact Podman/base-image provenance and licenses;
2. authorize a worker dependency/build/bootstrap correction;
3. produce SBOM/license and offline acquisition evidence;
4. pin clean-host requirements;
5. correct recipient documentation drift;
6. then execute clean-device isolation and synthetic PDF qualification.

Until those items are separately authorized and verified, PDF processing must remain unavailable and the current 503 fail-closed behavior is the correct state.
