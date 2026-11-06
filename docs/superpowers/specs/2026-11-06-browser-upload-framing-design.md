# Browser Upload Framing Correction Design

## Intent

Make ordinary browser PDF uploads work through the authenticated HTTPS tunnel while preserving the gateway's fail-closed security boundary, bounded memory/disk use, immutable application API v0.3 contract, and truthful client errors. The reported Safari upload failed before persistence because an HTTP/2 request without `Content-Length` was translated by ngrok to HTTP/1.1 chunked framing, which the gateway rejected. The gateway's rejection also omitted `X-Redaction-Lab-API: 0.3`, causing the UI to mislabel the transport rejection as a contract mismatch.

## Goals

- Accept a standards-conformant `Transfer-Encoding: chunked` body only for authenticated, exact-Origin `POST /api/v1/documents` requests without `Content-Length`.
- Decode the body under the existing `MAX_UPLOAD_BODY_BYTES` limit before opening the fixed loopback upstream request.
- Preserve exact body bytes and forward only `Content-Length`, never transfer encoding, credentials, cookies or forwarding headers.
- Bound memory with `SpooledTemporaryFile`; spill larger bodies to a private temporary file under process `umask 077` behavior.
- Return 413 for decoded overflow and 400 for malformed, truncated, extended, trailed, ambiguous or unsupported framing, without forwarding partial work.
- Make every handler-generated gateway error a valid API v0.3 JSON error so the frontend reports a public transport error rather than a false contract mismatch.
- Keep fixed-length upload streaming behavior unchanged and retain authentication before any body read.

## Non-goals

- No generic reverse proxy, arbitrary upstream, request retry, resumable upload, multi-user authorization, PDF parsing change, scoring change, model change or API schema version change.
- No acceptance of gzip/compressed transfer coding, chunk extensions, trailer fields, multiple transfer codings, `Content-Length` plus `Transfer-Encoding`, or chunked bodies on static/read/process routes.
- No buffering of fixed-length uploads that already stream safely.

## Constraints

- Application remains fixed at `127.0.0.1:8765`; gateway remains fixed at `127.0.0.1:8766` and authenticates before reading request bodies.
- Maximum decoded upload remains `MAX_UPLOAD_BODY_BYTES`; malformed input never reaches the application.
- Gateway concurrency remains bounded at eight. Each chunked upload may consume at most the configured body limit in a private spooled file, with only `_CHUNK` bytes retained in memory after spill.
- Reference content remains evaluation-only and no private documents, credentials, payloads or hostnames enter Git or test artifacts.

## Approaches considered

### 1. Require browsers/tunnel to add `Content-Length`

Rejected. Browser fetch APIs do not let application code set this forbidden header, and relying on one tunnel/browser implementation caused the current failure.

### 2. Teach the internal WSGI application to consume chunked bodies

Rejected. This would weaken and duplicate framing logic inside the trusted application boundary, where `wsgiref` has already normalized headers. It would also expose the local application to a transport mode needed only at the external edge.

### 3. Strict edge decode to a bounded spool, then fixed-length forwarding

Selected. The gateway retains raw framing visibility, authenticates and validates Host/Origin/route first, decodes one narrow transfer coding with a single authoritative implementation, and preserves the existing application contract. The disk-spool tradeoff is intentional: an upstream `Content-Length` cannot be known until the chunks are decoded. Owner-only concurrency and the existing 50 MiB pair bound keep resource use finite.

## Detailed behavior

Header validation distinguishes three request-body modes: no body, fixed `Content-Length`, and chunked upload. `Transfer-Encoding` is valid only when its single raw value is case-insensitively exactly `chunked`, no `Content-Length` exists, the method/path is the document upload route, exact multipart content type is present, and authentication/Host/Origin/route checks have already passed. All other transfer-encoding combinations fail 400.

The chunk decoder reads an ASCII hexadecimal size line bounded to 16 hex digits plus CRLF, rejects parameters/extensions, reads each chunk exactly, requires a trailing CRLF, counts decoded bytes before writing, and requires an immediate empty trailer section after the zero chunk. EOF, timeout, overlong lines, invalid sizes, chunk overflow, nonempty trailers and surplus ambiguity fail closed. Valid bytes are written to a `SpooledTemporaryFile(max_size=_CHUNK)`. Only after terminal validation does the gateway connect upstream, send the decoded length, and copy the spool in `_CHUNK` blocks.

Fixed-length uploads continue to connect upstream immediately and stream chunks without pre-buffering. Body-free routes continue to require zero length and reject transfer encoding.

Gateway `_reject` responses include `X-Redaction-Lab-API: 0.3`, JSON content type, bounded JSON error body, no-store, HSTS, no-referrer and nosniff. Authentication challenges remain present only on 401. The overload response is also emitted as the same bounded API-shaped JSON contract.

## Verification

- Raw-socket tests cover successful multi-chunk decoding, byte preservation, translated length and removed transport/auth headers.
- Security regressions cover authentication-before-read, fixed-length plus chunked ambiguity, unsupported codings/routes, extensions/trailers, malformed/truncated chunks, decoded overflow, timeout/cleanup and no upstream connection on failure.
- Error-contract tests prove gateway failures include API v0.3 and are consumable by the unchanged frontend error path.
- Existing fixed-length streaming test proves no regression.
- Full Python/Node/typecheck/build/audit verification and an external synthetic browser-framed upload prove the deployed path. User PDFs are not used for acceptance.

## Rollback

Stop the temporary tunnel/gateway, revert the correction commit normally, and relaunch the prior reviewed version. Existing immutable uploads and predictions are not altered. Rollback restores the known Safari upload limitation but does not corrupt stored evidence.
