-- Expand immutable reference evidence to the v3 worker without rewriting v2 history.
DROP TRIGGER reference_sources_insert_binding;
DROP TRIGGER reference_sources_no_update;
DROP TRIGGER reference_sources_no_delete;
DROP TRIGGER reference_job_ready_guard;
DROP TRIGGER reference_sources_no_replace;

CREATE TABLE reference_sources_v3 (
    source_id TEXT PRIMARY KEY,
    version_id TEXT NOT NULL UNIQUE REFERENCES document_versions(version_id),
    job_id TEXT NOT NULL UNIQUE REFERENCES application_jobs(job_id),
    project_id TEXT NOT NULL,
    input_sha256 TEXT NOT NULL CHECK (length(input_sha256) = 64),
    canonical_text TEXT NOT NULL CHECK (length(CAST(canonical_text AS BLOB)) <= 12582912),
    canonical_hash TEXT NOT NULL CHECK (length(canonical_hash) = 64),
    canonicalizer_version TEXT NOT NULL,
    page_count INTEGER NOT NULL CHECK (page_count BETWEEN 1 AND 100),
    request_nonce TEXT NOT NULL,
    protocol_version TEXT NOT NULL,
    image_digest TEXT NOT NULL,
    provenance TEXT NOT NULL CHECK (provenance = 'USER_SUPPLIED_EXPERIMENTAL'),
    CHECK (
        (protocol_version = 'pdf-worker-v2'
         AND canonicalizer_version = 'safe-exact-visible-text-v1')
        OR
        (protocol_version = 'pdf-worker-v3'
         AND canonicalizer_version IN (
             'safe-exact-visible-text-v1', 'ocr-reference-text-v1'
         ))
    )
);

INSERT INTO reference_sources_v3
SELECT * FROM reference_sources;
DROP TABLE reference_sources;
ALTER TABLE reference_sources_v3 RENAME TO reference_sources;

CREATE TRIGGER reference_sources_insert_binding BEFORE INSERT ON reference_sources
WHEN NOT EXISTS (
    SELECT 1 FROM application_jobs j JOIN document_versions v
      ON j.document_version_id = v.version_id
    WHERE j.job_id = NEW.job_id AND v.version_id = NEW.version_id
      AND j.status = 'PROCESSING' AND j.role = 'REFERENCE' AND v.role = 'REFERENCE'
      AND j.project_id = NEW.project_id AND v.project_id = NEW.project_id
      AND j.input_sha256 = NEW.input_sha256 AND v.sha256 = NEW.input_sha256
      AND j.request_nonce = NEW.request_nonce AND j.protocol_version = NEW.protocol_version
      AND j.image_digest = NEW.image_digest AND j.page_count = NEW.page_count
)
BEGIN SELECT RAISE(ABORT, 'reference source binding mismatch'); END;
CREATE TRIGGER reference_sources_no_update BEFORE UPDATE ON reference_sources
BEGIN SELECT RAISE(ABORT, 'reference sources are immutable'); END;
CREATE TRIGGER reference_sources_no_delete BEFORE DELETE ON reference_sources
BEGIN SELECT RAISE(ABORT, 'reference sources are immutable'); END;
CREATE TRIGGER reference_job_ready_guard BEFORE UPDATE ON application_jobs
WHEN NEW.role = 'REFERENCE' AND NEW.status = 'READY'
 AND NEW.protocol_version IN ('pdf-worker-v2', 'pdf-worker-v3')
 AND NOT EXISTS (SELECT 1 FROM reference_sources s WHERE s.job_id = NEW.job_id
                 AND s.version_id = NEW.document_version_id
                 AND s.page_count = NEW.page_count
                 AND s.protocol_version = NEW.protocol_version)
BEGIN SELECT RAISE(ABORT, 'READY reference requires immutable reference source'); END;
CREATE TRIGGER reference_sources_no_replace BEFORE INSERT ON reference_sources
WHEN EXISTS (SELECT 1 FROM reference_sources s WHERE s.version_id = NEW.version_id
             OR s.source_id = NEW.source_id OR s.job_id = NEW.job_id)
BEGIN SELECT RAISE(ABORT, 'reference sources are immutable'); END;
