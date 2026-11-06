# Experimental local application and owner-only gateway

This API v0.3 package serves the exact hash-bound React workspace and supports
isolated PDF processing, genuine local Qwen2.5 1.5B predictions, and versioned
experimental text-agreement scores. Reference text is evaluation-only.
`verified_score` remains null and the interface says **EXPERIMENTAL — NOT
SCIENTIFICALLY VALIDATED**. Missing, partial, ambiguous, unreadable or mismatched
truth stays Accuracy unknown. This single-model demonstration does not satisfy
the eventual commercial multi-model research requirement.

The PDF v2 and model runtimes have synthetic engineering qualification on the
reference Mac. They are **not bundled**, and this is not a clean-device installer,
scientific validation, institutional permission or a permanent hosted service.
The API health response retains `DEGRADED / runtime_qualified: false` to avoid
claiming recipient/release qualification; runtime identity is actually checked
again before each explicit processing operation.

## Existing prerequisites

Use native macOS arm64 CPython **3.12.14** with every dependency version in
[manifest.json](manifest.json). Source, production assets and both runtime locks
must be the reviewed package. The existing application-owned Podman machine must
be running, rootless and without host shares. Exact pinned model files and the
signed Ollama payload must exist. Launch never downloads dependencies, builds
images, starts Podman, opens a browser, or opens an external tunnel. An explicit
process action may start the owned loopback Ollama runtime, which is supervised
and stopped after the request. Ollama port `11434` must never be exposed.

`REDACTION_LAB_RUNTIME_ROOT` may point to the absolute trusted `runtime` directory
containing `pdf-worker/` and `model-runtime/`. This lets a separate synthetic
workspace reuse installed artifacts without copying gigabytes. Both runtimes
use the same owner/no-symlink/no-group-or-world-write root validation; full
inventories, executable identity, runtime policy and image checks remain.
Without this variable, legacy application-relative runtime paths remain valid.

## Check and launch locally

1. Open **Finder → Applications → Utilities → Terminal**. Type `cd `, drag the
   reviewed package folder into Terminal, and press **Return**.
2. Select the existing interpreter and private synthetic data/runtime paths:

   ```sh
   export REDACTION_LAB_PYTHON="/absolute/path/to/existing/environment/bin/python"
   export REDACTION_LAB_RUNTIME_ROOT="/absolute/path/to/trusted/runtime"
   export REDACTION_LAB_HOME="/absolute/path/to/dedicated/synthetic-workspace"
   ```

   Replace the example paths. Use a dedicated data directory outside the source
   checkout, not your home directory or a directory containing unrelated files.
3. Run `sh packaging/local/launch.sh --check`. This read-only check validates the
   platform/pins, lock hashes, API version, exact frontend inventory, storage
   safety, configured runtime inventories and optional gateway configuration.
   It does not execute either runtime or create application state.
   `runtime_files_verified: true` attests files, not live readiness. Missing or
   changed runtime files fail closed. Without an explicit runtime root, the
   diagnostic-only launch remains available and processing still re-attests.
4. Run `sh packaging/local/launch.sh`. Open `http://127.0.0.1:8765/` in the browser.
   Choose the generated redacted PDF and optionally its matching reference,
   click **Upload documents**, then **Process or resume saved document**.
   The PDF view shows locally selected files. Restored results require selecting
   the files again for preview; the server does not return saved PDF bytes.
5. Press **Control-C** in Terminal to stop the application. Restarting with the
   same data directory restores immutable uploaded bytes, jobs and results.
   Refresh/reconnect uses GET only and cannot generate another attempt.

The default local address is literal `127.0.0.1:8765`; `localhost`, IPv6 and
cross-origin mutations are rejected. A different `REDACTION_LAB_PORT` is allowed
for local diagnostics only. The gateway mode requires API port 8765. Storage
uses private directories, umask 077, descriptor-confined artifact access and
pre-migration backups. No deletion command is supplied. Keep private research
PDFs, raw payloads and credentials out of this public repository.

## Owner-only HTTPS demonstration

The controller opens the external tunnel only after exact-candidate review and
integration. The demonstration is one workspace, protected by a private
username/password at both the gateway and tunnel edge. Anyone given those
credentials could access that workspace. Do not share them with other users;
store generated synthetic documents only. The link works only while the Mac is
awake and the application, gateway, Podman machine and tunnel are running.

Store private configuration outside Git, in an owner-only directory with mode
0700 and a configuration file with mode 0600. Load these variables privately:

- `REDACTION_LAB_GATEWAY=1`
- `REDACTION_LAB_PUBLIC_HOST`: the exact lowercase assigned DNS hostname, without
  scheme, port, slash or trailing dot.
- `REDACTION_LAB_GATEWAY_USERNAME`: 1–64 ASCII letters/digits or `._-`.
- `REDACTION_LAB_GATEWAY_PASSWORD`: a generated 24–256 character printable ASCII
  secret without spaces. Do not pass it on command lines or place it in a URL.

Run preflight and launch as above. The application and gateway reserve both
`127.0.0.1:8765` and `127.0.0.1:8766` before creating state. Invalid credentials,
wrong configuration or occupied ports stop launch. No actual host or secret is
printed. Stop the launcher to close both listeners.

With the existing authenticated ngrok installation and private Basic-auth
traffic policy, the controller's tunnel command is:

```sh
ngrok http http://127.0.0.1:8766 \
  --url "https://$REDACTION_LAB_PUBLIC_HOST" \
  --inspect=false --traffic-policy-file "/absolute/private/path/policy.yml"
```

Use HTTPS ingress only. Preserve the original Host and Authorization headers;
do not use `--host-header=rewrite`, expose the application/model directly, or
remove either authentication boundary. The actual private edge policy and
hostname are operator configuration, never package artifacts. Inspect the
installed CLI help if its policy syntax changes. Final external acceptance must
prove unauthenticated access fails, authenticated assets/API succeed, wrong
origins cannot mutate, uploads/process/results work, and reconnect does not
create a second attempt. Local simulated TLS testing is not that final proof.

## Gateway and static boundaries

The standard-library gateway has one fixed destination: `127.0.0.1:8765`.
It listens only on `127.0.0.1:8766`, authenticates before reading an upload, checks
exact Host and HTTPS Origin (required for POST), allowlists application routes,
rejects duplicated/ambiguous framing and transfer encoding, and limits active
connections to eight. Uploads stream in 64 KiB chunks with the API's 50 MiB pair
plus multipart-overhead limit. Response bodies are bounded; large responses
spill into a private temporary file before complete framing is accepted.
Redirects, arbitrary destinations and Ollama routes are rejected. Only validated
requests receive translated local Host/Origin headers; credentials, cookies and
forwarding headers never reach the application. Security/content headers are
preserved and HSTS is added. Request bodies, URLs and credentials are not logged.

Only `/` and exact manifest-listed JS/CSS assets are served. No source maps,
filesystem routes, directory listing or fallback route exist. Trusted ownership,
no-follow descriptor traversal, single-link files, exact paths/size/hash/MIME,
32-file/4-MiB-per-file/8-MiB-total limits and immutable in-memory snapshots bind
the bundle. Missing or changed assets leave API diagnostics usable. Content
security policy permits same-origin scripts/styles/connections and local blob
PDF frames, with no inline script/eval/CDN. Other protections include no-store,
nosniff, no-referrer and denied outer framing.

## Delivery checklist

- [x] API v0.3 and exact frontend inventory are bound together.
- [x] Gateway raw-HTTP RED/GREEN tests and launch/auth/shutdown tests pass.
- [x] Trusted shared runtime-root checks preserve isolated synthetic storage.
- [x] Exact v2 image source/dependency/license inventory and protocol/isolation
      canaries independently requalified with no downloads.
- [x] Full combined genuine model/reference/evaluation and mounted-browser evidence
      on the reference host through a synthetic HTTPS origin mapped to loopback.
- [ ] Independent exact-candidate whole-branch review and normal integration.
- [ ] Final authenticated external HTTPS acceptance and owner delivery.
- [ ] Offline prerequisite/runtime bundle and clean second-device acceptance.
- [ ] Scientific model roster, private-data authority and scoring validation.

Exact commands, counts, runtime identities, failures/corrections and remaining
launch work belong to the task-scoped handoff and controller review record.
