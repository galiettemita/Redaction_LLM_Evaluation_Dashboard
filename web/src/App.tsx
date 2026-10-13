import { useEffect, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError, presentResults, restoreHandle, serializeHandle, validatePdf } from './api';
import type { AcceptedUpload, Handle, Health, Snapshot, createApi } from './api';
import { generateTemporaryPredictions } from './temporaryPrediction';

const STORAGE_KEY = 'redaction-lab:document-handle:v1';
function readSaved(): Handle | null {
  try { return restoreHandle(window.localStorage.getItem(STORAGE_KEY)); } catch { return null; }
}
function safeMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : 'This action could not finish. Refresh the saved document status.';
}
const jobLabels = { ACCEPTED: 'Uploaded · waiting to process', PROCESSING: 'Processing document', READY: 'Document ready',
  NO_REDACTIONS: 'No supported text redactions', UNSUPPORTED: 'Unsupported document', FAILED: 'Document processing failed' };

export default function App({ api }: { api: ReturnType<typeof createApi> }) {
  const [handle, setHandle] = useState<Handle | null>(readSaved);
  const [health, setHealth] = useState<Health | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [accepted, setAccepted] = useState<AcceptedUpload | null>(null);
  const [project, setProject] = useState('local-research');
  const [redacted, setRedacted] = useState<File | null>(null);
  const [reference, setReference] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [recoveryVersion, setRecoveryVersion] = useState('');
  const [recoveryJob, setRecoveryJob] = useState('');
  const [demoText, setDemoText] = useState('');
  const [demoError, setDemoError] = useState('');
  const [demoResult, setDemoResult] = useState<ReturnType<typeof generateTemporaryPredictions> | null>(null);
  const readController = useRef<AbortController | null>(null);
  const actionInFlight = useRef(false);
  const mounted = useRef(true);

  async function refresh(saved: Handle | null = handle) {
    readController.current?.abort();
    const controller = new AbortController();
    readController.current = controller;
    setBusy(true); setError('');
    // Clear the previous snapshot so an unsuccessful refresh cannot present stale
    // results as current. Refresh/reconnect only issue GET requests.
    setSnapshot(null);
    try {
      const [nextHealth, nextSnapshot] = await Promise.all([
        api.health(controller.signal), saved ? api.snapshot(saved, controller.signal) : Promise.resolve(null),
      ]);
      if (controller.signal.aborted || !mounted.current) return;
      setHealth(nextHealth); setSnapshot(nextSnapshot);
    } catch (failure) {
      if (!controller.signal.aborted && mounted.current) { setHealth(null); setError(safeMessage(failure)); }
    } finally {
      if (!controller.signal.aborted && mounted.current) setBusy(false);
    }
  }
  useEffect(() => {
    mounted.current = true;
    void refresh(handle);
    return () => { mounted.current = false; readController.current?.abort(); };
    // api is a stable instance supplied at startup; initial recovery must not
    // replay upload/process actions. Later reads are explicit user actions.
  }, [api]);

  function remember(saved: Handle): void {
    setHandle(saved);
    try {
      window.localStorage.setItem(STORAGE_KEY, serializeHandle(saved));
      setNotice('Document and job IDs saved in this browser. Refresh restores status without starting new work.');
    } catch {
      setNotice('This browser cannot save recovery IDs. Copy the document and job IDs below before closing.');
    }
  }
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (actionInFlight.current || busy) return;
    actionInFlight.current = true; setBusy(true); setError(''); setNotice('');
    try {
      const receipt = await api.upload(project.trim(), redacted, reference);
      if (!mounted.current) return;
      setAccepted(receipt); setSnapshot(null);
      const saved = { version_id: receipt.redacted.version_id, job_id: receipt.redacted.job_id };
      remember(saved);
      await refresh(saved);
    } catch (failure) { if (mounted.current) setError(safeMessage(failure)); }
    finally { actionInFlight.current = false; if (mounted.current) setBusy(false); }
  }
  function choose(file: File | null, role: 'redacted' | 'reference') {
    setError('');
    try { validatePdf(file, false); } catch (failure) { setError(safeMessage(failure)); }
    if (role === 'redacted') setRedacted(file); else setReference(file);
  }
  async function recover(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const saved = restoreHandle(JSON.stringify({ schema: 1, version_id: recoveryVersion.trim(), job_id: recoveryJob.trim() }));
    if (!saved) { setError('Enter valid document and job IDs.'); return; }
    setAccepted(null); remember(saved); await refresh(saved);
  }
  function generateDemo(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setDemoError(''); setDemoResult(null);
    try { setDemoResult(generateTemporaryPredictions(demoText)); }
    catch (failure) { setDemoError(failure instanceof Error ? failure.message : 'The demo could not generate candidates. Check the text limits below.'); }
  }
  function clearDemo() {
    setDemoText(''); setDemoError(''); setDemoResult(null);
  }
  const view = snapshot ? presentResults(snapshot.results) : null;
  return <>
    <a className="skip-link" href="#workspace">Skip to workspace</a>
    <header className="topbar">
      <a className="brand" href="#workspace" aria-label="Redaction Lab workspace"><span aria-hidden="true" className="brand-mark">▰</span> Redaction Lab</a>
      <span className="local-badge">Local workspace</span>
    </header>
    <main id="workspace" tabIndex={-1}>
      <div className="intro"><p className="eyebrow">Document research</p><h1>Every passage. Clear uncertainty.</h1>
        <p>Upload a redacted PDF and, optionally, a matching reference. Follow the saved document’s progress here.</p>
      </div>
      <section className="runtime-banner" aria-labelledby="runtime-title">
        <h2 id="runtime-title">{health ? 'Document processing unavailable' : 'Checking local service'}</h2>
        <p>{health ? 'This installation’s PDF processing has not been qualified. Uploads can be accepted, but processing and AI predictions are unavailable.' :
          error ? 'The local service could not be checked. Use Refresh status after starting the approved local service.' : 'Connecting to the local service. No document processing starts on reconnect.'}</p>
        <button type="button" className="secondary" disabled={busy} onClick={() => void refresh()}>Refresh status</button>
      </section>
      <div role="status" aria-live="polite" className="notice">{busy ? 'Working with the local service…' : notice}</div>
      {error ? <div role="alert" className="error"><h2>Action could not finish</h2><p>{error}</p></div> : null}
      <div className="workspace-grid">
        <section className="panel" aria-labelledby="upload-title">
          <div className="section-heading"><span className="step" aria-hidden="true">1</span><h2 id="upload-title">Add your documents</h2></div>
          <form onSubmit={upload} aria-busy={busy}>
            <fieldset disabled={busy}><legend className="visually-hidden">PDF upload</legend>
              <label htmlFor="project">Project ID</label><input id="project" value={project} onChange={e => setProject(e.target.value)} required maxLength={128} pattern="[A-Za-z0-9_-]+" aria-describedby="project-help" />
              <p id="project-help" className="hint">A local label using letters, numbers, hyphens or underscores.</p>
              <label htmlFor="redacted">Redacted PDF <span className="required">Required</span></label>
              <input id="redacted" type="file" accept=".pdf,application/pdf" required onChange={e => choose(e.target.files?.[0] ?? null, 'redacted')} aria-describedby="file-help" />
              <label htmlFor="reference">Matching reference PDF <span className="optional">Optional</span></label>
              <input id="reference" type="file" accept=".pdf,application/pdf" onChange={e => choose(e.target.files?.[0] ?? null, 'reference')} aria-describedby="reference-help file-help" />
              <p id="reference-help" className="hint">Adding a reference does not establish trustworthy revealed text or verified accuracy.</p>
              <p id="file-help" className="hint">PDF only · 25 MiB per file · up to 100 pages at processing. Use synthetic or explicitly authorized documents.</p>
              <button type="submit" disabled={!redacted || !health}>Upload documents</button>
            </fieldset>
          </form>
          <p className="privacy-note">Uploads go to this installation’s local service. Files and their text are not saved in browser storage.</p>
          <details><summary>Restore an existing document</summary>
            <p className="hint">Restoring reads saved status. It does not upload again or start processing.</p>
            <form onSubmit={recover}><fieldset disabled={busy}><legend className="visually-hidden">Recovery IDs</legend>
              <label htmlFor="restore-version">Document ID</label><input id="restore-version" value={recoveryVersion} onChange={e => setRecoveryVersion(e.target.value)} required maxLength={128} pattern="[A-Za-z0-9_-]+" />
              <label htmlFor="restore-job">Job ID</label><input id="restore-job" value={recoveryJob} onChange={e => setRecoveryJob(e.target.value)} required maxLength={128} pattern="[A-Za-z0-9_-]+" />
              <button type="submit" className="secondary">Restore status</button>
            </fieldset></form>
          </details>
        </section>
        <section className="panel document-panel" aria-labelledby="document-title">
          <div className="section-heading"><span className="step" aria-hidden="true">2</span><h2 id="document-title">Document workspace</h2></div>
          {handle ? <>
            <div className="document-state"><span className="state-dot" aria-hidden="true" />{snapshot ? jobLabels[snapshot.job.status] : 'Saved document · status not current'}</div>
            <dl className="metadata"><dt>Document ID</dt><dd>{handle.version_id}</dd><dt>Job ID</dt><dd>{handle.job_id}</dd>
              {accepted ? <><dt>Reference</dt><dd>{accepted.reference ? 'Uploaded · truth unknown' : 'Not uploaded'}</dd></> : null}
              {snapshot ? <><dt>Pages</dt><dd>{snapshot.document.page_count === null ? 'Not established' : snapshot.document.page_count}</dd></> : null}
            </dl>
            <div className="preview-placeholder"><span className="document-icon" aria-hidden="true">▤</span><h3>Local PDF preview unavailable</h3><p>A safe browser viewer has not been qualified in this source-only release. Previewing cannot establish targets or revealed truth.</p></div>
            <button type="button" className="secondary" disabled aria-describedby="process-help">Process document</button>
            <p id="process-help" className="hint">PDF processing is unavailable on this installation. Upload acceptance is separate from processing.</p>
            <details><summary>Document details</summary><p className="hint">Saved identifiers refer to this installation. Browser refresh reads stored state; it does not create a new run.</p>
              {snapshot ? <dl className="metadata"><dt>SHA-256</dt><dd>{snapshot.document.sha256}</dd><dt>Bytes</dt><dd>{snapshot.document.byte_size}</dd>
                <dt>Processing state</dt><dd>{snapshot.document.processing_status}</dd></dl> : null}
            </details>
          </> : <div className="preview-placeholder"><span className="document-icon" aria-hidden="true">▤</span><h3>Your document will appear here</h3><p>Upload a redacted PDF to obtain a document ID and follow its processing status.</p></div>}
        </section>
      </div>
      <section className="panel results-panel" aria-labelledby="results-title">
        <div className="section-heading"><span className="step" aria-hidden="true">3</span><h2 id="results-title">Results</h2></div>
        <div className="result-header"><h3>{view?.heading ?? 'No current results'}</h3><span className="unknown-badge">Accuracy unknown</span></div>
        <p>{view?.detail ?? 'Upload or restore a document, then refresh its saved status. Predictions are not available through this API.'}</p>
        <dl className="score-grid"><div><dt>Per redaction</dt><dd>{view?.targetScore ?? 'Not available'}</dd></div><div><dt>Per document</dt><dd>{view?.documentScore ?? 'Not available'}</dd></div><div><dt>Per model</dt><dd>{view?.modelScore ?? 'Not available'}</dd></div></dl>
        <p className="hint">No verified or experimental score is available. Missing, partial, unreadable or uncertain reference text means unknown accuracy.</p>
        <details><summary>Research context</summary><p>Only text passages can be reconstruction targets. Images, tables and wholly withheld pages are excluded. Document readiness is not prediction success, and a timeout or processing failure is not a factual error.</p><p>Trustworthy scoring and scientific validation remain pending. This interface displays the frozen API v0.1 response; it does not calculate accuracy.</p></details>
      </section>
      <section className="panel demo-panel" aria-labelledby="demo-title">
        <div className="demo-heading"><h2 id="demo-title">Experimental text-only demo</h2><span className="unvalidated-badge">UNVALIDATED</span></div>
        <p id="demo-warning" className="demo-warning">Plausible guesses are not proven correct. This temporary demo uses simple local rules, not PDF processing or AI/model inference. It creates no scores or research evidence.</p>
        <form onSubmit={generateDemo} aria-describedby="demo-warning">
          <label htmlFor="demo-text">Manually entered demo text</label>
          <textarea id="demo-text" rows={5} value={demoText} aria-describedby={demoError ? 'demo-help demo-error' : 'demo-help'} aria-invalid={demoError ? true : undefined}
            onChange={e => { setDemoText(e.target.value); setDemoError(''); setDemoResult(null); }}
            placeholder="Synthetic example: The meeting took place in [REDACTED]." />
          <p id="demo-help" className="hint">Enter synthetic or explicitly authorized plain text with 1–8 literal [REDACTED] markers. Limit: 4,000 UTF-8 bytes. Markup is rejected. Uploaded PDFs and references never fill this field.</p>
          <div className="demo-actions"><button type="submit">Generate demo candidates</button><button type="button" className="secondary" onClick={clearDemo}>Clear text and remove results</button></div>
        </form>
        {demoError ? <p id="demo-error" className="demo-error" role="alert">{demoError}</p> : null}
        <div className="demo-results" role="status" aria-live="polite" aria-atomic="true">
          {demoResult ? <>
            <h3>Unvalidated candidate phrases</h3>
            <dl className="demo-metadata"><dt>Demo status</dt><dd>{demoResult.status}</dd>
              <dt>Truth</dt><dd>{demoResult.truth_status} · accuracy unknown</dd>
              <dt>Score status</dt><dd>{demoResult.score_status} · no scoring</dd>
              <dt>Verified score</dt><dd>{String(demoResult.verified_score)} · not available</dd>
              <dt>Experimental score</dt><dd>{String(demoResult.experimental_score)} · not available</dd>
            </dl>
            <div className="demo-markers">{demoResult.markers.map(marker => <section className="demo-marker" key={marker.marker_index} aria-labelledby={`demo-marker-${marker.marker_index}`}>
              <h4 id={`demo-marker-${marker.marker_index}`}>Marker {marker.marker_index}</h4>
              <p className="hint">Rule basis: {marker.basis} Candidates are alternatives, not recovered hidden text.</p>
              <ol>{marker.candidates.map((candidate, index) => <li key={index}>{candidate}</li>)}</ol>
            </section>)}</div>
          </> : null}
        </div>
        <p className="hint">Demo text and candidates stay in this page’s memory. Clear them here or reload to remove them; they are not sent to the local API or saved in browser storage.</p>
      </section>
      <footer>Local, code-only interface · API v0.1 · Independent review pending</footer>
    </main>
  </>;
}
