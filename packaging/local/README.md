# Local API demo package

This candidate starts the merged Task 7B API on your own macOS Apple Silicon
computer. It is an API diagnostic demo: PDF processing is unavailable because
the PDF-worker runtime is unqualified; prediction and evaluation models are
unavailable; accuracy remains unknown and numeric scores remain null.

The baseline has no reviewed and merged frontend build artifact. `web/dist` is
outside Task 7C's authorized files. Serving frontend assets requires later
integration/Task 7D authority. Opening `/` returns the API's JSON 404; the health
endpoint is a diagnostic, not the website. This package is neither a standalone
installer nor evidence of clean recipient-device acceptance, runtime isolation,
model availability or scientific validity.

## Prerequisites and pins

Use macOS on Apple Silicon, with a native arm64 CPython **3.12.14** environment.
Intel Macs, Rosetta interpreters, Linux and Windows are unsupported by this
candidate. The general project minimum is Python 3.11; this candidate deliberately
requires the narrower tested version. The exact direct and transitive dependency
versions are in [manifest.json](manifest.json). They were captured from an existing
compatible environment and are candidate reproducibility pins, not approval of a
production stack or software license inventory. Preflight checks every listed
version and imports the application from this package's `src` directory.

No account, credentials, API keys, Node, Podman or model artifacts are needed for
this degraded API demo. Scripts never install, download, build images, create
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

   Exit 0 with `state: DEGRADED` means the API prerequisites matched. It does not
   mean PDF processing works. Error codes identify incompatible platform/Python,
   missing or mismatched dependencies, unsafe storage, or a changed worker lock.
   Preflight creates no data directory or database and makes no runtime calls.
5. After the candidate has the necessary review and local-use authority, launch:

   ```sh
   sh packaging/local/launch.sh
   ```

6. In a browser's address bar, type `http://127.0.0.1:8765/api/v1/health` and press
   **Return**. Expect API version `0.1`, `mode: local`, `state: DEGRADED` and
   `runtime_qualified: false`. Use `127.0.0.1`; `localhost`, another host, IPv6 or
   cross-origin requests are rejected. No browser is opened automatically.
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
manifest pins the unchanged, unverified worker lock by SHA-256; changing or
qualifying the lock requires a separately authorized, reviewed package. The
existing API refuses processing before claiming a job when that lock is
unverified, returning 503 `RUNTIME_UNVERIFIED`; uploads remain accepted with
unknown truth, empty targets and null scores. Refreshing, reading health or
restarting does not dispatch a paid run. No inference path is connected.

## Candidate evidence checklist

- [x] Manifest records platform, interpreter/dependency pins and unavailable gates.
- [x] Read-only preflight and literal loopback launcher implemented.
- [x] Synthetic script checks cover prerequisites, unsafe storage and runtime lock.
- [x] Synthetic loopback API checks cover upload, fail-closed processing, null
      results, Host/Origin rejection and restart persistence in a copied package.
- [ ] Independent exact-candidate QA/security review and owner merge authorization.
- [ ] Frontend integration and full browser workflow.
- [ ] Offline prerequisite bundle, SBOM/license inventory and PDF runtime qualification.
- [ ] Clean second-device recipient acceptance and authorized real models.

Completed test execution and exact candidate SHAs are recorded in the unique
Task 7P Packaging handoff; these checks do not settle the pending gates above.
