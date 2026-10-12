CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    designation TEXT NOT NULL CHECK (designation IN ('REDACTED', 'REFERENCE')),
    lifecycle_state TEXT NOT NULL CHECK (lifecycle_state = 'ACCEPTED'),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS document_versions (
    version_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    project_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('REDACTED', 'REFERENCE')),
    artifact_key TEXT NOT NULL,
    sha256 TEXT NOT NULL CHECK (length(sha256) = 64),
    byte_size INTEGER NOT NULL CHECK (byte_size > 0),
    media_type TEXT NOT NULL CHECK (media_type = 'application/pdf'),
    page_count INTEGER CHECK (page_count BETWEEN 1 AND 100),
    processing_state TEXT NOT NULL CHECK (
        processing_state IN ('ACCEPTED', 'READY', 'NO_REDACTIONS', 'UNSUPPORTED', 'FAILED')
    ),
    source_id TEXT,
    created_at TEXT NOT NULL,
    UNIQUE (project_id, role, sha256),
    UNIQUE (project_id, artifact_key, role)
);

CREATE TABLE IF NOT EXISTS document_pairs (
    pair_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    redacted_version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    reference_version_id TEXT REFERENCES document_versions(version_id),
    pairing_status TEXT NOT NULL CHECK (pairing_status = 'ASSOCIATED_UNTRUSTED'),
    created_at TEXT NOT NULL,
    UNIQUE (project_id, redacted_version_id, reference_version_id)
);

CREATE TABLE IF NOT EXISTS application_jobs (
    job_id TEXT PRIMARY KEY,
    request_digest TEXT NOT NULL UNIQUE,
    project_id TEXT NOT NULL,
    document_version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    role TEXT NOT NULL CHECK (role IN ('REDACTED', 'REFERENCE')),
    input_sha256 TEXT NOT NULL CHECK (length(input_sha256) = 64),
    status TEXT NOT NULL CHECK (
        status IN ('ACCEPTED', 'PROCESSING', 'READY', 'NO_REDACTIONS', 'UNSUPPORTED', 'FAILED')
    ),
    owner TEXT,
    request_nonce TEXT,
    protocol_version TEXT,
    image_digest TEXT,
    page_count INTEGER CHECK (page_count BETWEEN 1 AND 100),
    source_id TEXT,
    reason_code TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    checksum TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS one_active_document_job
ON application_jobs ((1)) WHERE status = 'PROCESSING';

CREATE TRIGGER IF NOT EXISTS documents_no_update BEFORE UPDATE ON documents
BEGIN SELECT RAISE(ABORT, 'documents are immutable'); END;
CREATE TRIGGER IF NOT EXISTS documents_no_delete BEFORE DELETE ON documents
BEGIN SELECT RAISE(ABORT, 'documents are immutable'); END;

CREATE TRIGGER IF NOT EXISTS document_versions_identity_no_update
BEFORE UPDATE OF version_id, document_id, project_id, role, artifact_key,
    sha256, byte_size, media_type, created_at ON document_versions
BEGIN SELECT RAISE(ABORT, 'document version identity is immutable'); END;
CREATE TRIGGER IF NOT EXISTS document_versions_state_guard
BEFORE UPDATE OF page_count, processing_state, source_id ON document_versions
WHEN OLD.processing_state != 'ACCEPTED'
  OR NEW.processing_state NOT IN ('READY', 'NO_REDACTIONS', 'UNSUPPORTED', 'FAILED')
  OR (NEW.role = 'REFERENCE' AND NEW.source_id IS NOT NULL)
  OR (NEW.role = 'REDACTED' AND NEW.processing_state = 'READY' AND NEW.source_id IS NULL)
  OR (NEW.processing_state != 'READY' AND NEW.source_id IS NOT NULL)
BEGIN SELECT RAISE(ABORT, 'invalid document version transition'); END;
CREATE TRIGGER IF NOT EXISTS document_versions_no_delete BEFORE DELETE ON document_versions
BEGIN SELECT RAISE(ABORT, 'document versions are immutable'); END;

CREATE TRIGGER IF NOT EXISTS document_pairs_no_update BEFORE UPDATE ON document_pairs
BEGIN SELECT RAISE(ABORT, 'document pairs are immutable'); END;
CREATE TRIGGER IF NOT EXISTS document_pairs_no_delete BEFORE DELETE ON document_pairs
BEGIN SELECT RAISE(ABORT, 'document pairs are immutable'); END;

CREATE TRIGGER IF NOT EXISTS application_jobs_identity_no_update
BEFORE UPDATE OF job_id, request_digest, project_id, document_version_id,
    role, input_sha256, created_at ON application_jobs
BEGIN SELECT RAISE(ABORT, 'application job identity is immutable'); END;
CREATE TRIGGER IF NOT EXISTS application_jobs_state_guard
BEFORE UPDATE ON application_jobs
WHEN NOT (
    (OLD.status = 'ACCEPTED' AND NEW.status = 'PROCESSING'
     AND NEW.owner IS NOT NULL AND NEW.reason_code IS NULL)
    OR
    (OLD.status = 'PROCESSING' AND NEW.status = 'PROCESSING'
     AND NEW.owner = OLD.owner AND NEW.request_nonce IS NOT NULL
     AND NEW.protocol_version IS NOT NULL AND NEW.image_digest IS NOT NULL
     AND OLD.request_nonce IS NULL AND OLD.protocol_version IS NULL
     AND OLD.image_digest IS NULL)
    OR
    (OLD.status = 'PROCESSING'
     AND NEW.status IN ('READY', 'NO_REDACTIONS', 'UNSUPPORTED', 'FAILED')
     AND NEW.owner = OLD.owner
     AND (NEW.status != 'READY' OR NEW.role = 'REFERENCE' OR NEW.source_id IS NOT NULL)
     AND (NEW.role != 'REFERENCE' OR NEW.source_id IS NULL)
     AND (NEW.status = 'READY' OR NEW.source_id IS NULL))
)
BEGIN SELECT RAISE(ABORT, 'invalid application job transition'); END;
CREATE TRIGGER IF NOT EXISTS application_jobs_no_delete BEFORE DELETE ON application_jobs
BEGIN SELECT RAISE(ABORT, 'application jobs are immutable'); END;

CREATE TRIGGER IF NOT EXISTS schema_migrations_no_update BEFORE UPDATE ON schema_migrations
BEGIN SELECT RAISE(ABORT, 'schema migrations are immutable'); END;
CREATE TRIGGER IF NOT EXISTS schema_migrations_no_delete BEFORE DELETE ON schema_migrations
BEGIN SELECT RAISE(ABORT, 'schema migrations are immutable'); END;
