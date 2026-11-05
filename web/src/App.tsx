import { useEffect, useReducer, useRef, useState } from 'react';
import type { FormEvent } from 'react';
import { ApiError, EXPERIMENTAL_LABEL, attemptCopy, createPdfPreview, keyboardTarget, presentResults, restoreHandle, scoreCopy, serializeHandle, validatePdf, workspaceTransition } from './api';
import type { Counts, Evaluation, Handle, Health, PredictionTarget, Results, Snapshot, Summary, createApi } from './api';

const STORAGE_KEY = 'redaction-lab:document-handle:v1';
const targetKey = (row: PredictionTarget) => `${row.target_id}:${row.target_version}`;
function readSaved(): Handle | null {
  try { return restoreHandle(window.localStorage.getItem(STORAGE_KEY)); } catch { return null; }
}
function safeMessage(error: unknown) {
  return error instanceof ApiError ? error.message : 'This action could not finish. Refresh the saved document status.';
}
function usePdf(file: File | null) {
  const [url, setUrl] = useState<string | null>(null);
  useEffect(() => {
    const preview = createPdfPreview();
    setUrl(preview.select(file));
    return preview.dispose;
  }, [file]);
  return url;
}
export function PdfPanel({url, release, page}: {url: string | null; release: 'redacted' | 'reference'; page: number}) {
  return url ? <div className="pdf-viewer">
    <iframe title={release === 'redacted' ? 'Redacted PDF preview' : 'Reference PDF preview'} src={release === 'redacted' ? `${url}#page=${page}` : url} />
    <p className="hint">Preview of your selected local file. Use the PDF toolbar to move between pages. {release === 'reference' ? 'Reference pagination may differ; locate the passage independently.' : 'Target selection opens its redacted page.'}</p>
    <a href={url} target="_blank" rel="noreferrer">Open selected PDF in a new tab</a>
  </div> : <div className="preview-placeholder"><span aria-hidden="true">▤</span><h3>Select a PDF to preview</h3>
    <p>Saved results can be restored, but select the PDF again to view it here. PDF bytes are not recovered from the server.</p></div>;
}
function CountList({counts}: {counts: Counts}) {
  return <dl className="counts">{([
    ['requested', 'Requested'], ['eligible', 'Eligible'], ['scored', 'Scored'], ['unknown', 'Unknown'], ['excluded', 'Excluded'], ['technical_failures', 'Technical failures'],
  ] as const).map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{counts[key]}</dd></div>)}</dl>;
}
function Score({evidence}: {evidence: Evaluation | Summary | null}) {
  return <div className="score-block"><p className="experimental-badge">{EXPERIMENTAL_LABEL}</p>
    <p className="score">{scoreCopy(evidence?.experimental_score ?? null)}</p>
    <p className="hint">{evidence?.scale ?? '0–100 text agreement'} · Verified accuracy unknown</p>
    {evidence ? <p className="method">Method: {evidence.method_id}</p> : null}
  </div>;
}
export function ResultsPanel({results, selected, onSelect}: {results: Results; selected: string | null; onSelect: (key: string) => void}) {
  const view = presentResults(results);
  const unique = [...new Map(results.targets.map(row => [targetKey(row), row])).values()];
  const chosen = unique.some(row => targetKey(row) === selected) ? selected : unique[0] ? targetKey(unique[0]) : null;
  const rows = results.targets.filter(row => targetKey(row) === chosen);
  return <section className="results-panel" aria-labelledby="results-title">
    <div className="section-heading"><p className="eyebrow">Stored evidence</p><h2 id="results-title">Passages & results</h2></div>
    <h3>{view.heading}</h3><p>{view.detail}</p>
    <div className="progress" role="status" aria-live="polite"><strong>{results.progress.terminal} / {results.progress.total} attempts finished</strong>
      <span>{results.progress.pending} pending · {results.progress.running} running</span></div>
    <CountList counts={results.counts} />
    <p className="hint">Technical failures can overlap eligible or unknown counts. They are not factual errors. Excluded candidates never enter a score denominator.</p>
    {unique.length ? <><nav className="target-list" aria-label="Select a redaction">{unique.map((row, index) => <button type="button" className="target-button" key={targetKey(row)}
      aria-pressed={chosen === targetKey(row)} onClick={() => onSelect(targetKey(row))}
      onKeyDown={event => {
        const next = keyboardTarget(unique.map(targetKey), targetKey(row), event.key);
        if (next) { event.preventDefault(); onSelect(next); const buttons = event.currentTarget.parentElement?.querySelectorAll<HTMLButtonElement>('button'); buttons?.[unique.findIndex(item => targetKey(item) === next)]?.focus(); }
      }}>Passage {index + 1}<span>Page {row.page_index + 1}</span></button>)}</nav>
      <div className="comparison">{rows.map(row => <article className="prediction-card" key={row.attempt_id}>
        <h3>{row.model_id}</h3><p className="hint">Configuration: {row.model_config_id} · Page {row.page_index + 1}</p>
        <p className="attempt-state">{attemptCopy(row.attempt_status)}</p>
        <h4>Model prediction</h4><p className="passage">{row.prediction ?? 'No prediction text is available. This technical outcome is not an incorrect factual answer.'}</p>
        <h4>Matching reference passage</h4><blockquote>{row.mapping?.exact_revealed_text ?? 'Accuracy unknown — no complete, reliably aligned reference passage is available.'}</blockquote>
        <p className="hint">{row.mapping?.explanation ?? 'Reference evidence has not been processed or no reference was supplied.'}</p>
        <Score evidence={row.evaluation} />
        {results.summaries.target.filter(summary => summary.target_id === row.target_id && summary.target_version === row.target_version && summary.model_id === row.model_id && summary.model_config_id === row.model_config_id).map(summary => <div key={summary.summary_id}>
          <CountList counts={summary.counts} /><p className="hint">Redaction scored-cell denominator: <strong>{summary.denominator}</strong></p>
        </div>)}
        {row.evaluation?.reason ? <p className="hint">Evaluation unavailable: {row.evaluation.reason.replaceAll('_', ' ').toLowerCase()}.</p> : null}
        {row.evaluation?.warnings.length ? <ul className="warning-list" aria-label="Critical-detail warnings">{row.evaluation.warnings.map(warning => <li key={warning}>{warning}</li>)}</ul> : null}
        <details><summary>Method & provenance details</summary>
          <dl className="metadata"><dt>Target / version</dt><dd>{row.target_id} / {row.target_version}</dd><dt>Attempt</dt><dd>{row.attempt_id}</dd>
            <dt>Request hash</dt><dd>{row.request_hash}</dd><dt>Response hash</dt><dd>{row.response_hash ?? 'Unavailable'}</dd>
            <dt>Mapping</dt><dd>{row.mapping ? `${row.mapping.mapping_id} / ${row.mapping.mapping_version}` : 'Unavailable'}</dd>
            <dt>Verified score</dt><dd>null · unknown</dd></dl>
          {row.evaluation?.subscores ? <dl className="subscores">{Object.entries(row.evaluation.subscores).map(([key, value]) => <div key={key}><dt>{key.replaceAll('_', ' ')}</dt><dd>{typeof value === 'boolean' ? (value ? 'Yes' : 'No') : value.toFixed(3)}</dd></div>)}</dl> : null}
          {row.evaluation?.applied_caps.length ? <p>Critical-detail caps: {row.evaluation.applied_caps.join(', ')} / 100.</p> : null}
        </details>
      </article>)}</div></> : <p>No completed model attempts are stored yet.</p>}
    <div className="summary-grid">{(['document', 'model'] as const).map(level => <section className="summary-level" key={level} aria-label={`${level} summaries`}>
      <h3>{level === 'document' ? 'Document agreement' : 'Model agreement'}</h3>
      {results.summaries[level].length ? results.summaries[level].map(summary => <article className="summary-card" key={summary.summary_id}>
        <h4>{summary.model_id}</h4><p className="hint">Configuration: {summary.model_config_id}</p><Score evidence={summary} /><CountList counts={summary.counts} />
        <p>{level === 'model' ? 'Scored-document denominator' : 'Scored-cell denominator'}: <strong>{summary.denominator}</strong>{level === 'model' ? ` · ${summary.document_count} document(s) in this selected set` : ''}</p>
      </article>) : <p>Accuracy unknown · no stored {level} summary.</p>}
    </section>)}</div>
    <p className="method-note">Agreement averages include only scored answers. They are not recovery rates over every requested passage. Lexical agreement can miss paraphrases and reversed roles; it cannot establish historical correctness.</p>
  </section>;
}

export default function App({api}: {api: ReturnType<typeof createApi>}) {
  const [handle, setHandle] = useState<Handle | null>(readSaved);
  const [health, setHealth] = useState<Health | null>(null);
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [project, setProject] = useState('local-research');
  const [redacted, setRedacted] = useState<File | null>(null);
  const [reference, setReference] = useState<File | null>(null);
  const [fileEpoch, setFileEpoch] = useState(0);
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState('');
  const [recoveryVersion, setRecoveryVersion] = useState('');
  const [recoveryJob, setRecoveryJob] = useState('');
  const [workspace, dispatch] = useReducer(workspaceTransition, {release: 'redacted', selected: null, actionError: '', readError: ''});
  const redactedUrl = usePdf(redacted), referenceUrl = usePdf(reference);
  const readController = useRef<AbortController | null>(null);
  const actionInFlight = useRef(false);
  const mounted = useRef(true);
  const actionError = (message: string) => dispatch({type: 'action-error', message});
  async function refresh(saved: Handle | null = handle) {
    readController.current?.abort();
    const controller = new AbortController(); readController.current = controller;
    setBusy(true); setSnapshot(null);
    try {
      const [nextHealth, nextSnapshot] = await Promise.all([api.health(controller.signal), saved ? api.snapshot(saved, controller.signal) : Promise.resolve(null)]);
      if (controller.signal.aborted || !mounted.current) return;
      setHealth(nextHealth); setSnapshot(nextSnapshot); dispatch({type: 'refreshed'});
    } catch (failure) {
      if (!controller.signal.aborted && mounted.current) { setHealth(null); dispatch({type: 'read-error', message: safeMessage(failure)}); }
    } finally { if (!controller.signal.aborted && mounted.current) setBusy(false); }
  }
  useEffect(() => {
    mounted.current = true; void refresh(handle);
    return () => { mounted.current = false; readController.current?.abort(); };
    // Startup/reconnect is GET-only. Upload and process are explicit actions.
  }, [api]);
  function remember(saved: Handle) {
    setHandle(saved);
    try { window.localStorage.setItem(STORAGE_KEY, serializeHandle(saved)); setNotice('Recovery IDs saved. Refresh restores results without starting work.'); }
    catch { setNotice('Copy the document and job IDs before closing; this browser cannot save them.'); }
  }
  async function upload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy || actionInFlight.current) return;
    actionInFlight.current = true; setBusy(true); actionError('');
    try {
      const receipt = await api.upload(project.trim(), redacted, reference);
      if (!mounted.current) return;
      const saved = {version_id: receipt.redacted.version_id, job_id: receipt.redacted.job_id};
      dispatch({type: 'select', selected: null}); remember(saved); await refresh(saved);
    } catch (failure) { if (mounted.current) actionError(safeMessage(failure)); }
    finally { actionInFlight.current = false; if (mounted.current) setBusy(false); }
  }
  function choose(file: File | null, role: 'redacted' | 'reference') {
    try { validatePdf(file, false); }
    catch (failure) { actionError(safeMessage(failure)); file = null; }
    if (role === 'redacted') setRedacted(file); else {
      setReference(file); if (!file) dispatch({type: 'release', release: 'redacted', available: true});
    }
  }
  async function recover(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (busy || actionInFlight.current) return;
    const saved = restoreHandle(JSON.stringify({schema: 1, version_id: recoveryVersion.trim(), job_id: recoveryJob.trim()}));
    if (!saved) { actionError('Enter valid document and job IDs.'); return; }
    setRedacted(null); setReference(null); setFileEpoch(value => value + 1);
    dispatch({type: 'release', release: 'redacted', available: true}); dispatch({type: 'select', selected: null}); remember(saved); await refresh(saved);
  }
  async function processDocument() {
    if (!handle || busy || actionInFlight.current) return;
    actionInFlight.current = true; setBusy(true); actionError(''); setNotice('Processing the saved document. Genuine inference can take several minutes.');
    try { await api.process(handle.job_id); if (mounted.current) setNotice('Processing finished. Stored results refreshed.'); }
    catch (failure) { if (mounted.current) actionError(safeMessage(failure)); }
    finally { if (mounted.current) await refresh(handle); actionInFlight.current = false; if (mounted.current) setBusy(false); }
  }
  const selected = snapshot?.results.targets.find(row => targetKey(row) === workspace.selected) ?? snapshot?.results.targets[0];
  return <>
    <a className="skip-link" href="#workspace">Skip to workspace</a>
    <header className="topbar"><a className="brand" href="#workspace"><span aria-hidden="true">▰</span> Redaction Lab</a><span className="local-badge">Experimental research workspace</span></header>
    <main id="workspace" tabIndex={-1}>
      <div className="intro"><p className="eyebrow">Read the document. Inspect the evidence.</p><h1>Every passage. Clear uncertainty.</h1>
        <p>Compare genuine model predictions with matching revealed text, while keeping uncertainty visible.</p></div>
      <div className="experimental-banner"><strong>{EXPERIMENTAL_LABEL}</strong><p>One installed local model: Qwen2.5 1.5B. Experimental text agreement is an unvalidated lexical measure. Verified accuracy remains unknown.</p></div>
      <section className="runtime-banner" aria-labelledby="runtime-title"><div><h2 id="runtime-title">{health ? 'Local service connected' : workspace.readError ? 'Service connection unavailable' : 'Connecting to service'}</h2>
        <p>{health ? 'Runtime integrity is checked before PDF processing and model inference. Scientific and recipient validation remain pending.' : 'Reconnect reads saved state only.'}</p></div>
        <button type="button" className="secondary" disabled={busy} onClick={() => void refresh()}>Refresh status</button></section>
      <div role="status" aria-live="polite" className="notice">{busy ? notice || 'Reading the service…' : notice}</div>
      {workspace.actionError ? <div role="alert" className="error"><strong>Action could not finish</strong><p>{workspace.actionError}</p><button type="button" className="secondary" onClick={() => actionError('')}>Dismiss action error</button></div> : null}
      {workspace.readError ? <p role="alert" className="error">Status refresh failed: {workspace.readError}</p> : null}
      <div className="workspace-grid">
        <aside className="panel intake" aria-labelledby="upload-title"><h2 id="upload-title">Documents</h2>
          <form onSubmit={upload}><fieldset disabled={busy}><legend className="visually-hidden">Upload PDF documents</legend>
            <label htmlFor="project">Project ID</label><input id="project" value={project} onChange={e => setProject(e.target.value)} required maxLength={128} pattern="[A-Za-z0-9_-]+" />
            <label htmlFor="redacted">Redacted PDF · required</label><input key={`redacted-${fileEpoch}`} id="redacted" type="file" accept=".pdf,application/pdf" required onChange={e => choose(e.target.files?.[0] ?? null, 'redacted')} />
            <label htmlFor="reference">Matching reference · optional</label><input key={`reference-${fileEpoch}`} id="reference" type="file" accept=".pdf,application/pdf" onChange={e => choose(e.target.files?.[0] ?? null, 'reference')} />
            <p className="hint">PDF only · 25 MiB per file · up to 100 pages. Use synthetic or explicitly authorized documents.</p>
            <button type="submit" disabled={!redacted || !health}>Upload documents</button>
          </fieldset></form>
          <p className="hint">Selecting files previews them locally. Upload creates the saved pair. Selecting a different file does not change saved results.</p>
          <details><summary>Restore a saved document</summary><form onSubmit={recover}><fieldset disabled={busy}><legend className="visually-hidden">Recovery identifiers</legend>
            <label htmlFor="restore-version">Document ID</label><input id="restore-version" value={recoveryVersion} onChange={e => setRecoveryVersion(e.target.value)} required maxLength={128} />
            <label htmlFor="restore-job">Job ID</label><input id="restore-job" value={recoveryJob} onChange={e => setRecoveryJob(e.target.value)} required maxLength={128} />
            <button type="submit" className="secondary">Restore status</button></fieldset></form></details>
          {handle ? <details><summary>Saved document details</summary><dl className="metadata"><dt>Document ID</dt><dd>{handle.version_id}</dd><dt>Job ID</dt><dd>{handle.job_id}</dd><dt>Pages</dt><dd>{snapshot?.document.page_count ?? 'Not established'}</dd><dt>Processing</dt><dd>{snapshot?.document.processing_status ?? 'Status not current'}</dd></dl></details> : null}
        </aside>
        <section className="panel document-panel" aria-labelledby="document-title"><div className="viewer-header"><h2 id="document-title">Document workspace</h2>
          <div className="release-toggle" role="group" aria-label="PDF release"><button type="button" aria-pressed={workspace.release === 'redacted'} onClick={() => dispatch({type: 'release', release: 'redacted', available: true})}>Redacted</button>
            <button type="button" disabled={!referenceUrl} aria-pressed={workspace.release === 'reference'} aria-describedby="reference-view-help" onClick={() => dispatch({type: 'release', release: 'reference', available: !!referenceUrl})}>Reference</button></div></div>
          <p id="reference-view-help" className="hint">{referenceUrl ? 'Switching releases preserves the selected target. Reference material is evaluation-only.' : 'Select the matching reference PDF to enable its local preview.'}</p>
          <p className="file-name">{workspace.release === 'redacted' ? redacted?.name : reference?.name}</p>
          <PdfPanel url={workspace.release === 'redacted' ? redactedUrl : referenceUrl} release={workspace.release} page={(selected?.page_index ?? 0) + 1} />
          <button type="button" disabled={busy || !snapshot || !['ACCEPTED', 'READY'].includes(snapshot.job.status)} onClick={() => void processDocument()}>Process or resume saved document</button>
          <p className="hint">Runs the saved upload through isolated PDF processing and genuine local inference. Existing attempts are preserved. Refresh never starts work.</p>
        </section>
      </div>
      {snapshot ? <ResultsPanel results={snapshot.results} selected={workspace.selected} onSelect={key => dispatch({type: 'select', selected: key})} /> : <section className="panel"><h2>Passages & results</h2><p>Upload or restore a document to read its stored results. Accuracy unknown.</p></section>}
      <footer>API v0.3 · Reference text never enters model prediction inputs · Text passages only</footer>
    </main>
  </>;
}
