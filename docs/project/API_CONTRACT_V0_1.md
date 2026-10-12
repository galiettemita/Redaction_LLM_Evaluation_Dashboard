# Redaction Lab local API v0.1 — frozen E0052

Baseline f943d72f177c8f3f418ff38af030c5ea8107ade7. Local same-origin, 127.0.0.1 only. JSON errors {error:{code,message}}; never expose local paths/raw errors. Max 25 MiB per PDF, 50 MiB pair, 100 pages at processing, one job, 60s worker budget. Unverified PDF runtime must fail closed and create no authoritative source. Reference optional for prediction, uploads do not confer trusted truth. Numeric scores remain null unless separately scientifically approved.

GET /api/v1/health -> {api_version:'0.1',state:'READY'|'DEGRADED',runtime_qualified:false,mode:'local'}.
POST /api/v1/documents multipart project_id, redacted_pdf, optional reference_pdf -> 201 {pair_id,project_id,redacted:{version_id,job_id,sha256,byte_size,status:'ACCEPTED'},reference:null|{version_id,sha256,byte_size},truth_status:'UNKNOWN'}.
GET /api/v1/documents/{version_id} -> {version_id,role,sha256,byte_size,processing_status,page_count,job_id,reason_code,source_id}.
GET /api/v1/jobs/{job_id} -> {job_id,version_id,status,reason_code,source_id}.
POST /api/v1/jobs/{job_id}/process -> {job_id,status,reason_code,source_id}; if runtime unverified return 503 {error:{code:'RUNTIME_UNVERIFIED',message:'PDF processing runtime is not qualified on this installation'},job_id,status:'ACCEPTED'} and do not claim job.
GET /api/v1/results/{version_id} -> {version_id,status:'PENDING'|'UNSUPPORTED'|'NO_REDACTIONS'|'FAILED'|'NEEDS_REVIEW'|'AVAILABLE',targets:[],summaries:{target:null,document:null,model:null},score_status:'NONE',verified_score:null,experimental_score:null,truth_status:'UNKNOWN'}. Do not fabricate targets or scores.

Reject unsafe Host/Origin/Content-Type and oversized streams. No deletion or general download API. Errors: 400 invalid, 404 unknown, 409 conflict, 413 excessive bytes, 415 wrong type, 422 malformed, 503 runtime, 500 redacted error. Header X-Redaction-Lab-API: 0.1. Schema/route/dependency changes require owner amendment. No runtime install, inference or model calls permitted.
