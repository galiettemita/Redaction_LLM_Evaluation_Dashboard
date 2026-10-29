# Local website and API package

> **RL-WEB-008 frontend candidate — BUILT FOR API v0.2.** The exact production
> bundle is hash-bound in the local manifest and may launch in truthful
> `DEGRADED` mode. The PDF worker and local model locks are qualified only on
> the reference host; neither runtime is bundled with this candidate. This is not a complete recipient
> release or scientific validation.

This candidate starts the merged Task 7B API on your own macOS Apple Silicon
computer. It composes the verified API v0.2 frontend bundle on the same origin
as the API. The PDF worker and model runtime have synthetic-only qualification
evidence on the reference host, but are not bundled for a recipient. Accuracy
remains unknown and numeric scores remain null.

The manifest binds the reviewed v0.2 artifact under `web/dist` by exact paths,
sizes, SHA-256 hashes and MIME types; arbitrary builds are not accepted. This package is neither a standalone
installer nor evidence of clean recipient-device acceptance, runtime isolation,
model availability on another host or scientific validity. Exact local model
source, integrity, license and SBOM records are under `packaging/model-runtime`.

## Prerequisites and pins

Use macOS on Apple Silicon, with a native arm64 CPython **3.12.14** environment.
Intel Macs, Rosetta interpreters, Linux and Windows are unsupported by this
candidate. The general project minimum is Python 3.11; this candidate deliberately
requires the narrower tested version. The exact direct and transitive dependency
versions are in [manifest.json](manifest.json). They were captured from an existing
compatible environment and are candidate reproducibility pins, not approval of a
production stack or software license inventory. Preflight checks every listed
version and imports the application from this package's `src` directory.

No account, credentials, API keys, Node, Podman or model artifacts are bundled or
downloaded by this package. Scripts never install, download, build assets/images, create
VMs or start Podman. No prerequisite installation is authorized under Task 7P.
If an interpreter or dependency is missing or mismatched, stop and arrange a
separately authorized prerequisite environment. Do not change pins just to bypass
the check. A wheel archive, interpreter installer, SBOM/license inventory and
fully offline prerequisite bundle are not supplied. Once prerequisites exist,
these scripts require no internet connection.

## Check and launch

1. Receive the reviewed source package including `src/redaction_lab`, application
   migrations, `packaging/pdf-worker` and `packaging/local`. Extract it outside
   any existing application data directory. Paths containing spaces are supported.
2. Open **Finder → Applications → Utilities → Terminal**. Type `cd ` (including
   the space), drag the extracted package folder from Finder into Terminal, then
   press **Return**.
3. Select an existing, compatible Python interpreter. Replace the example path
   with your own prerequisite environment; this is not a bundled environment:

   ```sh
   export REDACTION_LAB_PYTHON="/absolute/path/to/your/existing/environment/bin/python"
   ```

4. Run the read-only check:

   ```sh
   sh packaging/local/launch.sh --check
   ```

   Exit 0 with `state: DEGRADED` means the API prerequisites and exact frontend bundle matched.
   `frontend_available: true` is emitted only after exact bundle verification;
   a changed or missing bundle reports false. It does not
   mean PDF processing works. Error codes identify incompatible platform/Python,
   missing or mismatched dependencies, unsafe storage, or a changed worker lock.
   Preflight creates no data directory or database and makes no runtime calls.
5. After the candidate has the necessary review and local-use authority, launch:

   ```sh
   sh packaging/local/launch.sh
   ```

6. Read the launcher output. If it prints `Verified frontend assets`, type
   `http://127.0.0.1:8765/` into your browser's address bar and press **Return**.
   If it prints `FRONTEND_UNAVAILABLE`, use
   `http://127.0.0.1:8765/api/v1/health` for the API diagnostic. Expect API
   version `0.2`, `mode: local`, `state: DEGRADED` and
   `runtime_qualified: false`. Use `127.0.0.1`; `localhost`, another host, IPv6 or
   cross-origin requests are rejected. No browser is opened automatically.
   Frontend availability never changes the API's degraded runtime status.
7. Return to Terminal and press **Control-C** to stop the API. Restarting with the
   same storage directory preserves uploaded synthetic bytes and accepted jobs.

You may choose another port with `export REDACTION_LAB_PORT="8766"`; use that
port in the diagnostic URL. The port must be 1–65535. An occupied port fails
before initializing storage. `REDACTION_LAB_HOST` must be exactly `127.0.0.1`;
the listening address is also hard-coded to that address. This single-process
standard-library server is a bounded local diagnostic service, not a production
HTTP server; it sets a 10-second socket timeout and suppresses access logs.

## Storage and safety boundaries

The default local data directory is
`~/Library/Application Support/RedactionLab`. To use a separate dedicated
directory, set a literal absolute path before checking and launching:

```sh
export REDACTION_LAB_HOME="/absolute/path/to/dedicated/redaction-lab-data"
```

Do not select your home directory, a shared directory, source checkout or an
existing directory containing unrelated files. Preflight rejects symlinked path
components and existing data roots without mode 0700. Launch uses Task 7A's
descriptor-confined directory/storage services and locked migration helper;
directories are private (0700), new files use umask 077, and required database
upgrades use the existing pre-migration backup behavior. Launch changes only
this dedicated state directory; preflight is read-only. Uploaded documents,
SQLite state, retained evidence and backups survive restart. No deletion or
automatic cleanup command is supplied here.

Use only synthetic data within current authorization. The repository was public;
never put private PDFs, datasets, credentials or raw model payloads into it.
Keep package/source files trusted and unchanged while the service runs. The
manifest pins the reference-host-qualified worker and model locks by SHA-256;
changing either lock requires a separately reviewed package. The API refuses
PDF processing or model dispatch when the corresponding application-owned
runtime is absent or differs, returning `RUNTIME_UNVERIFIED` or
`MODEL_RUNTIME_UNVERIFIED`. The model lock uses application-root-relative paths
and requires the exact signed executable, complete model-file inventory,
literal-loopback API version, provider model name and manifest digest before
dispatch. Unknown truth and both scores remain null.
Refreshing, reading results, or restarting does not dispatch a paid run.

## Static asset boundary

Only `/` and exact manifest-listed `/assets/<produced-name>.js` or `.css` routes
support GET/HEAD. There is no `/index.html` alias, directory listing, source-map
serving or fallback for unknown routes. Queries, encoded/absolute request targets,
static bodies, transfer encoding and duplicate singleton HTTP headers are
rejected. Successful HEAD responses carry the exact GET length and no body.
Normal `/api/v1` requests retain their existing API behavior; the HTTP handler
rejects ambiguous framing before WSGI, which has no chunked-body decoder.

The install root, manifest and frontend tree must belong to the launching
account and must not be writable by group/others. Every path component is
opened with directory descriptors and no-follow flags. Assets must be regular,
single-link files; missing, extra, symlinked, redirected, changed or incorrectly
hashed files fail frontend verification. Limits are 32 files, 4 MiB per file
and 8 MiB total. The only permitted dist entries are `index.html` and `assets`.
Bytes are validated once and retained as an immutable snapshot, so a later
filesystem modification cannot cause a request to read a different file.
Restart is required after an approved package update. No assets or upload data
share a filesystem route.

Static responses use exact MIME types, no-store, nosniff, no-referrer, denied
framing and a restrictive content-security policy allowing local scripts,
styles and connections only. No CDN, cross-origin fetch, inline script or eval
is enabled. Failed frontend verification leaves the API diagnostic usable;
an unsafe/invalid package manifest prevents launch entirely.

## Candidate evidence checklist

- [x] Manifest records platform, interpreter/dependency pins and unavailable gates.
- [x] Read-only preflight and literal loopback launcher implemented.
- [x] Synthetic script checks cover prerequisites, unsafe storage and runtime lock.
- [x] Synthetic loopback API checks cover upload, fail-closed processing, null
      results, Host/Origin rejection and restart persistence in a copied package.
- [x] Synthetic static GET/HEAD, exact bytes/MIME/length, security headers and
      routing/framing/confinement checks pass with a frozen fixture inventory.
- [x] Frontend verification fails closed and preserves API-only diagnostics.
- [x] Independent exact-candidate automated QA/security review passed.
- [x] Genuine API v0.2 frontend build, reviewed hash-pinned integration and
      synthetic headless-Chrome browser workflow.
- [x] Reference-host PDF worker and synthetic-only Ollama/model qualification.
- [x] Exact local model source, integrity, license and CycloneDX SBOM records.
- [ ] Offline prerequisite/runtime bundle and clean second-device recipient acceptance.
- [ ] Human-approved scientific model roster, private-data use and scoring validation.

Completed test execution and exact candidate SHAs are recorded in the unique
Task 7CP Packaging handoff; these checks do not settle the pending gates above.
