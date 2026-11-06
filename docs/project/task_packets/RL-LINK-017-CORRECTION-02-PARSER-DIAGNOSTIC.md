# RL-LINK-017 Correction 02 — recoverable PDF parser diagnostic

Task ID / state / single owner: RL-LINK-017-CORRECTION-02 / APPROVED and IN_PROGRESS by the owner's 2026-11-06 request to continue until the PDF error is removed / Codex Engineering Lead.

Objective / non-goals: Accept otherwise valid PDFs when pypdf repairs the known non-zero-indexed cross-reference table condition; retain fail-closed handling for unknown parser warnings and actual malformed input. Remove the resulting end-to-end processing failure for the owner's explicitly selected PDF pair. Do not broaden supported target types, change scoring semantics, expose document contents, or claim scientific validation.

Rxx requirements / DEC decisions / unresolved Dxx gates: R01–R12; DEC-001–DEC-023. Verified/scientific accuracy remains unknown and `verified_score` remains null. Experimental evaluation remains clearly labeled.

Baseline SHA / prerequisites: live GitHub `main` `baab7dfee13c2b6e6845f37cff9ee82f6dda58df`, coordination epoch E0073. Browser upload of the exact selected pair returned HTTP 201; processing deterministically returned `MALFORMED_PDF` because a recoverable pypdf warning was treated as fatal.

Inputs / outputs / exact contract versions: Existing API v0.3, detector output contract and runtime qualification format remain unchanged. Output is a narrowly classified parser diagnostic, regression evidence, rebuilt qualified PDF-worker image, deployed local demonstration, and end-to-end result evidence.

Allowed files, actions and artifact publication scope: `src/redaction_lab/pdf_detector.py`, `tests/test_pdf_detector.py`, PDF-worker qualification and local packaging manifests required by source-integrity policy, this packet, one task-scoped handoff, and checklist/state updates needed for truthful delivery. Offline container rebuild/qualification, local service restart, use of the owner-selected local PDFs without logging or publication, normal commits/push/PR/integration, and deployment to the existing owner-authenticated demonstration are authorized. No raw documents, credentials, or raw model payloads may enter Git.

Tests and acceptance evidence: TDD regression must fail before implementation and pass afterward. A known fixed-template pypdf repair diagnostic must not by itself produce `MALFORMED_PDF`; unknown parser warnings and malformed bytes must remain fail-closed; diagnostic text must remain suppressed. Run focused tests, full Python and frontend regressions, worker verification, authenticated HTTP/browser upload, processing, results retrieval, and restart/reconnect checks proportionate to the changed layers.

Data, provider, cost and runtime limits: No paid calls or new providers. Genuine local qualified models only. The owner-selected PDFs stay local/private and are used solely for this requested acceptance. No private content or derived payload is committed or printed.

Consumers and expected handoffs: Lead implementation and deployment handoff; exact-candidate independent reviewer verdict; owner receives the working link and recovery identifiers privately.

Independent reviewer / required human approvals: Independent exact-candidate engineering/security review is required before completion. The owner's direct correction request supplies product/runtime authority for this scope. Research validation, Columbia data authorization and permanent hosting remain outside scope.

Rollback / stop conditions: Fail closed if the diagnostic cannot be identified without inspecting or retaining document-bearing text, if unknown parser warnings become accepted, if worker qualification fails, or if the exact pair still fails. Roll back to the prior qualified image and deployment if runtime acceptance regresses.
