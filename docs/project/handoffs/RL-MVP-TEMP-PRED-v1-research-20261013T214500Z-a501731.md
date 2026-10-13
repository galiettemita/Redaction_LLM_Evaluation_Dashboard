# RL-MVP-TEMP-PRED-v1 Research / Evaluation independent review

Task ID: RL-MVP-TEMP-PRED-v1  
Role / session label: Research / Evaluation independent reviewer  
UTC time: 2026-10-13T21:45:00Z  
State: READY_FOR_REVIEW  
Review verdict: **PASS FOR TEMPORARY-PREDICTION RESEARCH/PROVENANCE SEMANTICS; NOT SCIENTIFIC VALIDATION**

Baseline integration SHA / decision epoch: `dbcf1b7d4e116ac56b3338de03ea64fb80066ca4` / E0060  
Exact implementation SHA reviewed: `a5017315c6cdb4b69b0503a32a2e49525530f4f9`  
Published implementation branch HEAD: `1df79a434002193013d7332bdd35c6219cc47cc0`  
Source requirements: AGENTS.md; CURRENT_STATE.md E0060; DECISIONS.md; AGENT_HANDOFF.md; `docs/project/task_packets/RL-MVP-TEMP-PRED-v1.md`; existing Task-4/Task-6/DEC-022 boundaries.
Authorization: exact-SHA independent Research review and one unique Research handoff only. No implementation edits, merge, deployment, dependencies, Podman/VM, private data, external providers, model inference or build/manifest changes.

## Exact scope / freshness

- Live `main` refreshed before review and before publication and remained `dbcf1b7d4e116ac56b3338de03ea64fb80066ca4` / E0060.
- Candidate differs from baseline in exactly the six authorized implementation paths:
  - `src/redaction_lab/temporary_prediction.py`
  - `tests/test_temporary_prediction.py`
  - `web/src/temporaryPrediction.ts`
  - `web/tests/temporaryPrediction.test.js`
  - `web/src/App.tsx`
  - `web/src/styles.css`
- Published branch HEAD adds only the unique implementation handoff.
- No API, Task-3/4/6, persistence/store, manifest, launcher, dist, dependency or lockfile changes.

## Research findings

### Explicit temporary/unvalidated status — PASS

Both Python and TypeScript helpers always return:
- `status: TEMPORARY_UNVALIDATED`;
- `truth_status: UNKNOWN`;
- `score_status: NONE`;
- `verified_score: null`;
- `experimental_score: null`.

The UI labels the panel “Experimental text-only demo” with an `UNVALIDATED` badge and explicitly states that plausible guesses are not proven correct.

No confidence, accuracy percentage, verified-recovery claim, model ranking or hidden-text certainty is produced.

### No authoritative Task-4 or Task-6 evidence — PASS

The new temporary helpers import/use no Task-4 source, run, attempt, worker, model-adapter or Task-6 evaluator/store/summary authority.

The feature does not create:
- PredictionSource records;
- ModelAttempt records;
- EvaluationRecord records;
- SummarySnapshot records;
- database writes;
- logs of snippets.

The panel remains in page memory only and clear/reload removes it.

### No reference-text contamination / DEC-022 promotion — PASS

The panel is manual-input only. The UI explicitly states that uploaded PDFs and references never fill the field.

No reference registry, reference mapping, trusted fixture, DEC-022 enrollment or revealed reference text enters either helper.

Therefore arbitrary references remain unrelated to these temporary guesses, and DEC-022 synthetic-only truth eligibility remains unchanged.

### No PDF-runtime bypass or model inference — PASS

The helpers operate only on a caller-supplied text string.

They perform no:
- PDF read/parsing;
- OCR;
- runtime worker call;
- provider/model call;
- network request;
- filesystem access.

The existing PDF upload/status/runtime-unverified pipeline remains untouched.

### Heuristic output is deliberately generic — PASS

Candidate phrases are generic category placeholders such as “a person,” “a place,” “a time,” and “an unknown detail,” with a displayed rule basis stating they are generic heuristics.

The UI further says: “Candidates are alternatives, not recovered hidden text.”

This is consistent with the packet's non-authority requirement.

### Null/unknown research semantics — PASS

No score interpretation is introduced. Missing truth remains UNKNOWN, not zero.

The temporary panel's output is scientifically separate from Task-6 NEEDS_REVIEW evidence and does not upgrade, overwrite or compete with existing evaluation state.

### Source-only/browser availability distinction — explicit

The current committed `web/dist` intentionally predates this feature. Therefore the new panel is source-complete but **not present in the packaged browser build** at this exact candidate.

That is an authorized E0060 limitation, not a provenance defect. A later separately approved build/manifest update would require its own review.

## Independent evidence actually run

### Exact repository suite

NOT RUN independently. This review environment still cannot obtain a local repository checkout through shell GitHub access. Backend-reported 30 Python / 10 focused Node / 32 all-Node / 624 full pytest and 6,191 same-session cross-language probes are implementation evidence only.

### Independent exact-source checks

GitHub exact-SHA inspection confirmed:
- TEMPORARY_UNVALIDATED status;
- UNKNOWN truth;
- NONE score status;
- both numeric scores null;
- no Task-4/6 authority imports/calls;
- no network calls in temporary helpers;
- no filesystem/browser-storage access in temporary helpers;
- exact literal `[REDACTED]` marker semantics;
- 4,000 UTF-8-byte bound;
- eight-marker bound;
- manual-only UI input;
- no upload/reference auto-fill;
- explicit UNVALIDATED/no-score warning.

Result: **13/13 source checks PASS**.

### Independent Python adversarial reproduction

Reproduced the exact Python helper logic locally from reviewed source.

Covered:
- three-marker cue behavior;
- deterministic repeatability;
- TEMPORARY_UNVALIDATED / UNKNOWN / NONE / null-score invariants;
- 1–8 marker bounds;
- wrong-case marker rejection;
- 4,000-byte UTF-8 boundary;
- markup/script/javascript-like rejection;
- Unicode long-s / surrogate rejection.

Result: **PASS assertions=19**.

This is an isolated reproduction of exact reviewed helper logic, not a full package execution.

## Tests not run / limitations

Not independently run:
- TypeScript helper execution;
- Python/TypeScript differential fuzzing;
- full pytest/Node suites;
- TypeScript typecheck/Vite build/browser rendering;
- HTML injection browser testing;
- packaged-browser visibility;
- private/real data;
- PDF/runtime/model/provider operations;
- scientific D03-D06 validation.

## Residual risks / acceptance boundaries

1. This feature is intentionally heuristic and must never be presented as recovered truth.
2. It is source-only until a separately authorized frontend build/asset assembly.
3. HTML/script safety in React relies on ordinary escaped text-node rendering; no independent browser security run was performed here.
4. Cross-language determinism was source-inspected and Python independently probed, but the implementer's 6,191 cross-language comparisons were not inherited as independent evidence.
5. D03/D04/D05/D06 remain NOT APPROVED.

## Verdict

**PASS** for RL-MVP-TEMP-PRED-v1 Research/provenance semantics on exact SHA `a5017315c6cdb4b69b0503a32a2e49525530f4f9`.

The feature remains explicitly temporary, unvalidated, unknown-truth and null-scored, with no reference contamination, PDF-runtime bypass, model inference or authoritative Task-4/Task-6 evidence.

This PASS is not scientific validation, QA/security certification, merge authorization or browser-build approval.

Independent review evidence: exact-SHA source inspection plus 19 independent Python assertions; author-reported test counts were not inherited.  
Next receiver: **Lead / Architect**, after a separate independent QA/security exact-SHA handoff is published.  
Rollback/correction: preserve history; any demonstrated defect requires additive correction and fresh exact-SHA review.  
Publication: PUBLISHED on `review/rl-mvp-temp-pred-v1-research-e0060`; not merged.
