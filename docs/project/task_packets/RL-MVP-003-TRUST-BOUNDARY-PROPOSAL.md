# RL-MVP-003 — Trust boundary decision proposal

State: PROPOSED; NOT AUTHORIZED for implementation.
Lead/Architect proposal for owner decision, 2026-10-08.
Baseline main 05ce31b07ff21f656dda8ae835cca2efd45a297b, E0026.
Backend branch remains at 2d79ee6a7d5ba2a06148ff257529faa50dfa06e1.
Backend reports local rejected candidate 80f9ee171c6923f9affb3a5259bf93105301e65a; NOT PUBLISHED, not independently inspected.

## Blocking fact

A stateless aligner can validate the SHA-256, role and project fields in a DocumentVersion but cannot establish whether an untrusted caller fabricated the record. A hash check verifies byte consistency, not trusted provenance or correct redacted/reference release pairing. Backend reports a false CONFIRMED adversarial probe using a fabricated record. Backend also reports partially covered edge punctuation incorrectly omitted with CONFIRMED. No code, merge or Task 4 is authorized while these remain.

## Recommended narrowly scoped October 12 option — requires owner approval

Introduce a small, application-owned registry/manifest of **pre-authorized synthetic PDF release pairs only**, generated or pinned by a trusted test-fixture bootstrap. Registry holds immutable project ID, redacted and reference document-version IDs, both SHA-256 hashes, explicit pair association and provenance. The aligner accepts only a registry-resolved trusted pair/opaque handle; never an arbitrary caller-constructed DocumentVersion as evidence of trust. It re-hashes the supplied PDF bytes and checks pair identity before considering CONFIRMED, then still requires unique, complete, readable, two-sided word alignment and exact target span. Unregistered or user-uploaded reference pairs remain NOT_SCOREABLE with null truth. This is **test-fixture trust**, not independent archival authenticity or Columbia data authorization.

A process-local manifest is not a security boundary against malicious code executing inside the trusted application. Keep untrusted uploads outside the registry and document that limitation. No cloud, provider calls or additional spending. New file scope, integration interface and benchmark impact require owner approval and a separate bounded implementation packet. Scientific D03 approval remains pending.

Alternative for full user-upload verified scoring: design a trusted authenticated intake and durable immutable pairing registry with access controls and provenance validation. This is broader and not covered by Task 3 or the October 12 schedule. A user-uploaded reference cannot become independently verified simply because the application stored its hash.

## Remaining Task-3 correction

Two-sided global evidence and exact edge punctuation/whitespace (or null truth) are still required. Preserve no-leakage, unknown/null, provenance and fresh independent QA/Research reviews. Do not publish the rejected candidate as verified or merge it.

Owner decision requested: approve synthetic-only trusted-pair registry for the October 12 demonstration and defer verified scoring for arbitrary uploaded references, OR request the broader authenticated intake design. Until then Task 3 is BLOCKED and the local rejected candidate is NOT PUBLISHED.
