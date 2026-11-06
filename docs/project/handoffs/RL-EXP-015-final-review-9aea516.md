# Final whole-branch review and single correction wave

Task ID: RL-EXP-015 / RL-LINK-017 final review of `9aea516`.

Role / session label: final reviewer findings supplied by Engineering Lead; correction evidence recorded by Task 6 implementer. This record does not attribute independent approval to the implementer.

UTC time: 2026-11-06 (2026-11-05 America/New_York).

State: reviewed candidate CHANGES_REQUESTED; corrected candidate READY_FOR_REVIEW. **NOT-YET-INTEGRATED** and no external HTTPS launch.

Baseline integration SHA / decision epoch: live main `cb0fa4f1242ae8bf12afb084bc9475017040b784` / E0072, DEC-023.

Candidate branch / exact commit SHA: reviewed `codex/finish-app` candidate `9aea516fc717140415fc1950dfc4bc8b7fb621c8`; correction implementation `9e6c01f4eb86503745b1cfc75cb366193283c3f3`. A subsequent documentation commit carries this durable record and updates the canonical handoff/index. Exact corrected-candidate independent re-review remains open.

Source requirements / approved decisions / contract versions: R01–R12, DEC-001..023; experimental-text-agreement-v1, API v0.3, pdf-worker-v2. Verified scores remain null. No research validation, private data or paid-resource authority is implied.

Authorization reference and permitted file/action scope: Lead's single final-wave instruction and [RL-LINK-017 amendment](../task_packets/RL-LINK-017-CONTROLLED-DEMO.md#final-whole-branch-review-correction-wave-2026-11-05). Scorer/literal evaluator tests, source-bound offline worker refresh, exact provenance, checklist/handoff correction and local synthetic acceptance only. No subagents, downloads, push, merge or tunnel.

Work performed / artifacts and exact paths:

| Review finding | Severity / reproduction | Correction and current disposition |
| --- | --- | --- |
| Whitespace-separated signs erase contradiction | Important: `score_text_agreement('Temperature was − 5 degrees.', 'Temperature was + 5 degrees.')` returned 100 with no cap. | `src/redaction_lab/experimental_scoring.py` retains ASCII/NFKC-normalized signs across whitespace before numeric extraction. Literal ASCII/U+2212/Unicode-space tests and evaluator tests prove cap 60; genuinely ambiguous `± 5` remains null. Correction implemented; independent re-review pending. |
| SBOM/interpreter/license completeness wording | Minor: package SBOM did not independently enumerate CPython and full license metadata. | Keep the 55-entry package/OS SBOM, explicitly distinguish observed CPython 3.12.16 and complete `/usr/local` file/link inventory. Package license annotations remain incomplete; the separate 21-file license hash inventory is not complete per-component licensing. Metadata, README and handoff wording corrected. |
| Historical attempt image attribution | Minor: initial14 attempts were not all on image 954ca79. | Exact split from stored redacted application-job image receipts: historical12 on 954ca79, two on f1b8a731. Final-wave image 03db44f has14 fresh attempts, separately recorded. Prior immutable rows unchanged. |
| Local checklists lagged evidence | Minor: RL-LINK-017 local items and Task 4 combined canary remained unchecked. | First seven local items and Task 4 Step 8 checked after current evidence; final independent review/integration/external HTTPS remain open. |
| Planned unchanged test paths lacked disposition | Minor: no Task 6 edits in three allowed test files. | Existing worker protocol/document tests through 16ae648 and static tests through 1f964db reused and rerun. Actual image qualification script and mounted Chrome provide additional acceptance. No cosmetic/fake edits. |

Durable review handoff requested by Lead: this file records the exact reviewed candidate, supplied findings, corrections and open independent acceptance gate; indexed in AGENT_HANDOFF.

Tests actually run / command / result / environment:

- Native arm64 CPython 3.12.14 and Node 24.21.0/npm 11.19.0 on the reference Mac, existing pinned dependencies.
- Scorer/evaluator focused RED: **12 failed / one passed / 68 deselected**. Failures covered both directions of ASCII signs, U+2212, NBSP/thin-space/tab/newline, equivalent same-signed quantities and evaluator cap propagation. Ambiguous-sign null was already correct.
- `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src /Users/galiettemita/Downloads/IARPA/Redaction_LLM_Evaluation_Dashboard-RUNTIME009B/.venv/bin/python -m pytest tests/test_experimental_scoring.py tests/test_evaluator.py tests/test_evaluation_store.py tests/application/test_evaluation_service.py -q`: **123 passed in 16.47s**.
- All-source inventory assertion rejected stale scorer hash before manifest refresh; `tests/application/test_isolation.py tests/security/test_pdf_worker_container.py`: **26 passed in 2.44s** after exact artifact refresh. Coverage includes all 38 source files, including SQL migrations.
- Same Python interpreter `-m pytest -q`: **956 passed in 37.84s**. `npm test --prefix web`: **55 passed**. `npm run build --prefix web`: typecheck/build pass with identical frontend hashes. `npm audit --prefix web --json`: zero vulnerabilities. Shell syntax and diff checks pass.
- Actual offline build with `--pull=never --network=none`; complete source and dependency inventories compared to exact installed bytes. Before build 14,830,002,176 bytes free; minimum during build 14,829,076,480; <=512 MiB projected increment and >=8 GiB monitor. No downloads/deletions of unrelated data.
- `scripts/verify-pdf-worker.sh` passed genuine redacted/reference protocol and bounds, hidden-text exclusion, non-root/no-network/read-only/no-capabilities/no-host-shares/resource checks, failure/deadline cleanup and the signed-quantity regression **inside the new image**. Clean machine restart repeated the complete script and production ApplicationPdfWorker attestation.

Final runtime identity:

| Artifact | Identity |
| --- | --- |
| v2 image | `sha256:03db44f11ea940fff0c75a94dc393aed73095e8ee71307afb4adc3ef0e290e34` |
| Manifest | `sha256:d90c5ec2c01ad84cc2949354e26f9a7140f23f5095956ea2100031904f9850ab` |
| Image size | 179,907,424 bytes |
| 38-file source inventory | `f11ab0192f3484c5789d4a61b9c302a3be3371985563df899dde1ce8e2d50e76` |
| Runtime lock SHA256 | `a5b576688a822aa06385cc788489866673f32dee003d77719af7331bd17c4100` |
| 3,216 dependency entries | `796918201c671074182df724ba7a42fb59f5628bfbb595897c90be5a8653ddc5` |
| 21 license-file hashes | `1048df2b689585e6b847f2150e30f59d46f13321fc0552b30877653a400d31b4` |

The exact v1 image remains dependency-byte provenance only; no inherited qualification. All source/dependency/image/SBOM/qualification/manifest records bind the new image. Original runtime advisory observations remain historical; this is not a new vulnerability scan of runtime dependencies.

Genuine combined acceptance and immutable history:

- Final image 03db44f: **14 fresh SUCCEEDED attempts** across seven declared two-target cases. Exact reference gives target 0/8.3 and document/model 4.2; requested 2 / eligible 2 / scored 2 / unknown 0. Marker, missing, mismatch, ambiguous and unreadable cases each give eligible 0 / scored 0 / unknown 2/null scores. Partial case gives PARTIAL/null for the hidden target and CONFIRMED/8.3 for the separate revealed target. All verified scores remain null; zero technical failures in these cases.
- Historical **12** SUCCEEDED attempts on `sha256:954ca79b9c06811911b3d68ceb90a3b7ca85bdb509b1e09b5c17ba7c1c603129`; historical **2** marker attempts on `sha256:f1b8a731643bc0691849d5f82761a7fe9d7f7e658a2c19eb4e94c3e2c6f54b39`. These do not count as final-image evidence.
- Snapshot comparison proves all prior 14 attempt rows, 14 evaluation rows and 28 summary rows unchanged; snapshot SHA256 `d3b8ed68b61ea9f197e4f91189dd32e93ead38a4b55d3be4eef8db93ab28657d`. No automatic re-evaluation or overwrite. All 28 prediction manifests exclude the reference-only marker. Every explicit resume preserves existing attempts.
- Fresh mounted Chrome run on the final image passed upload, local release toggle, process/busy/results, ArrowDown focus/selection, file replacement and invalid-file removal, blob cleanup, real disconnection error persistence after refresh, GET-only reload and same-attempt explicit resume. Four POST attempts: upload, intentionally disconnected process, successful process, same-attempt resume; no browser runtime exceptions. Loopback TLS test certificate/host mapping only; no actual external TLS claim.

Tests not run and reason: exact correction independent re-review is controller work; final external ngrok/TLS acceptance follows review/integration. No scientific study, new-device acceptance, private PDF, paid provider or additional model.

Independent review evidence: findings above are the Lead-supplied final whole-branch review of 9aea516. The implementer reproduced and corrected them; this is not independent acceptance of 9e6c01f or the documentation commit.

Research / data approval evidence: DEC-023 experimental-only generated synthetic data. D03–D06 scientific gates remain open; no verified numeric score.

Known issues / risks / stale dependencies: lexical agreement remains unvalidated and the small model produced low scores. Package license metadata is explicitly incomplete; separate inventories bind bytes. Final actual HTTPS acceptance remains mandatory. Previous stored evidence is historical and is not silently rescored after this bugfix.

Affected roles / requested next action: Lead obtains exact corrected-candidate acceptance, then normal integration and the authorized private external demonstration. Keep gateway on 127.0.0.1:8766 and never expose 11434. Update the remaining delivery checks only from actual evidence.

Last freshness check and relevant differences: live main remained `cb0fa4f1242ae8bf12afb084bc9475017040b784` before correction commit. Final source correction remains branch-only. Recheck before integration.

Rollback or correction approach: normal revert/correction of additive commits; preserve stored history. Changing any source again requires another exact image/source-inventory refresh. All task application/gateway/Ollama/browser/TLS services and the owned Podman machine were stopped; no listeners remained on 8765/8766/11434/18443, and disposable worker containers were cleaned. Final free space 19,014,897,664 bytes. No unrelated data removed.

Publication: committed locally on `codex/finish-app`; **NOT-YET-INTEGRATED**, not pushed/merged/deployed by this implementer.
