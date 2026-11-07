import { useEffect, useRef, useState } from 'react';

type Report = { interpretation?: string; baseline_correct?: number; cloaked_correct?: number; test_count?: number; drop_percentage_points?: number; [key: string]: unknown };
type Job = { status: string; message: string; report?: Report };

async function responseJSON(response: Response) {
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.error?.message || `Service error (${response.status}).`);
  return data;
}

export function FaceWorkspace() {
  const [ready, setReady] = useState(false);
  const [connection, setConnection] = useState('Checking Fawkes service…');
  const [mode, setMode] = useState('mid');
  const [kind, setKind] = useState('cloak');
  const [file, setFile] = useState<File | null>(null);
  const [target, setTarget] = useState('');
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [report, setReport] = useState<Report | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [original, setOriginal] = useState<string | null>(null);
  const controller = useRef<AbortController | null>(null);
  const jobId = useRef<string | null>(null);
  const generation = useRef(0);

  async function connect() {
    setReady(false);
    try {
      const response = await fetch('/api/face/health', { cache: 'no-store', signal: AbortSignal.timeout(8000) });
      const data = await responseJSON(response);
      if (data.method !== 'upstream-fawkes') throw new Error('Connect the Fawkes backend.');
      setReady(data.ready);
      setConnection(data.ready ? 'Fawkes service connected' : 'Fawkes service needs setup');
    } catch { setConnection('Fawkes offline — open the Face Cloak notebook and connect its configuration'); }
  }
  useEffect(() => { void connect(); return () => { ++generation.current; controller.current?.abort(); }; }, []);
  useEffect(() => () => { if (result) URL.revokeObjectURL(result); }, [result]);
  useEffect(() => () => { if (original) URL.revokeObjectURL(original); }, [original]);

  function reset() { setFile(null); setOriginal(null); setReport(null); setResult(null); setError(''); setMessage(''); setConsent(false); }
  async function run() {
    if (!file || !consent || busy || !ready) return;
    const current = ++generation.current;
    const abort = new AbortController(); controller.current = abort;
    setBusy(true); setResult(null); setReport(null); setError(''); setMessage('Sending to your configured Fawkes service…');
    try {
      const data = await responseJSON(await fetch(`/api/face/jobs?kind=${kind}&mode=${mode}&target=${encodeURIComponent(target)}`, {
        method: 'POST', body: file, headers: { 'Content-Type': kind === 'proof' ? 'application/zip' : file.type }, signal: abort.signal,
      }));
      jobId.current = data.id;
      const deadline = Date.now() + 45 * 60 * 1000;
      while (Date.now() < deadline) {
        if (abort.signal.aborted) throw new Error('Cancelled.');
        const job: Job = await responseJSON(await fetch(`/api/face/jobs/${data.id}`, { cache: 'no-store', signal: abort.signal }));
        if (current !== generation.current) return;
        setMessage(job.message);
        if (job.status === 'done') {
          const response = await fetch(`/api/face/jobs/${data.id}/result`, { signal: abort.signal });
          if (!response.ok) throw new Error('The result could not be downloaded.');
          const blob = await response.blob();
          if (current !== generation.current) return;
          setResult(URL.createObjectURL(blob)); setReport(job.report || null); return;
        }
        if (job.status === 'failed' || job.status === 'cancelled') throw new Error(job.message);
        await new Promise<void>((resolve, reject) => {
          const onAbort = () => { window.clearTimeout(timer); reject(new Error('Cancelled.')); };
          const timer = window.setTimeout(() => { abort.signal.removeEventListener('abort', onAbort); resolve(); }, 2000);
          abort.signal.addEventListener('abort', onAbort, { once: true });
        });
      }
      throw new Error('Experiment timed out.');
    } catch (reason) {
      if (jobId.current) void fetch(`/api/face/jobs/${jobId.current}`, { method: 'DELETE' });
      if (current === generation.current) { setMessage(''); setError(abort.signal.aborted ? 'Experiment cancelled.' : reason instanceof Error ? reason.message : 'Experiment failed.'); }
    } finally { if (current === generation.current) { setBusy(false); } }
  }

  return <section id="face-workspace" aria-labelledby="face-title">
    <div className="section-heading"><span className="eyebrow">FACE CLOAK / FAWKES</span><h2 id="face-title">Keep your face. Change what gets learned.</h2><p>Cloak face photos with upstream Fawkes, then measure recognition on separate, clean test photos. This protects against a specific training scenario; it is not Meta AI editing protection.</p></div>
    <div className="workspace-grid">
      <article className="image-card">
        <label htmlFor="face-task">What would you like to do?</label>
        <select id="face-task" value={kind} disabled={busy} onChange={e => { setKind(e.target.value); reset(); }}><option value="cloak">Cloak a face photo</option><option value="proof">Run a recognition experiment</option></select>
        {kind === 'proof' && <><p>Choose a ZIP with train and test folders. Use at least 3 people, 3 training photos and 2 different test photos per person. Every photo must contain exactly one face.</p><p className="metadata">Example: train/person_a/1.jpg and test/person_a/4.jpg. Repeat for person_b and person_c. ZIP the train and test folders together, without an outer folder. Maximum 60 photos / 64 MB.</p><label htmlFor="target-person">Identity to protect (folder name)</label><input id="target-person" value={target} disabled={busy} onChange={e => { setTarget(e.target.value); setResult(null); setReport(null); }} placeholder="person_a"/></>}
        <label className="file-label" htmlFor="face-file">{kind === 'cloak' ? 'Choose face photo' : 'Choose experiment ZIP'}</label>
        <input id="face-file" type="file" accept={kind === 'cloak' ? 'image/png,image/jpeg' : '.zip'} disabled={busy} onChange={e => {
          const selected = e.target.files?.[0]; setResult(null); setReport(null); setError(''); setConsent(false);
          if (!selected) return;
          if (selected.size > (kind === 'cloak' ? 10 : 64) * 1024 * 1024) { setFile(null); setOriginal(null); setError('This file is too large.'); return; }
          setFile(selected); setOriginal(kind === 'cloak' ? URL.createObjectURL(selected) : null);
        }}/>
        {original && <div className="preview"><img src={original} alt="Original face photo"/></div>}
        {file && <p className="metadata">Selected: {file.name}</p>}
      </article>
      <aside className="engine-card"><span className="eyebrow">TRAINING PRIVACY</span><h3>Measure the outcome.</h3><p role="status">{connection}</p><button className="text-button" disabled={busy} onClick={() => void connect()}>Check Fawkes connection</button>
        <label htmlFor="face-mode">Cloaking level</label><select id="face-mode" value={mode} disabled={busy} onChange={e => { setMode(e.target.value); setResult(null); setReport(null); }}><option value="low">Low</option><option value="mid">Medium</option><option value="high">High — may be more visible</option></select>
        <label className="consent"><input type="checkbox" checked={consent} disabled={busy} onChange={e => setConsent(e.target.checked)}/> I have permission to use these photos and agree to processing by the configured service. Temporary image files are deleted after the job; results remain available for up to 30 minutes or until removed.</label>
        <button className="primary" disabled={!ready || !file || !consent || busy || (kind === 'proof' && !target)} onClick={() => void run()}>{busy ? 'Experiment running…' : kind === 'cloak' ? 'Generate Fawkes cloak' : 'Run recognition experiment'}</button>
        {busy && <button className="text-button cancel" onClick={() => controller.current?.abort()}>Cancel experiment</button>}
        <p role="status">{message}</p><p role="alert" className="error">{error}</p>
        <p className="fine-print">A completed cloak is not a protection score. The recognition test fits a classifier on a frozen independent FaceNet encoder; it does not reproduce full model training or prove universal protection.</p>
      </aside>
    </div>
    {result && <article className="result-card"><div><span className="eyebrow">{kind === 'cloak' ? 'CLOAK GENERATED / UNVERIFIED' : 'MEASURED RECOGNITION EXPERIMENT'}</span><h3>{kind === 'cloak' ? 'Inspect your cloaked photo.' : 'Read the actual test outcome.'}</h3>
      {kind === 'proof' && report && <><table><thead><tr><th>Target identity</th><th>Correct / held-out photos</th></tr></thead><tbody><tr><td>Original training photos</td><td>{report.baseline_correct} / {report.test_count}</td></tr><tr><td>Cloaked training photos</td><td>{report.cloaked_correct} / {report.test_count}</td></tr></tbody></table><p>Recognition accuracy drop: {report.drop_percentage_points?.toFixed(1)} percentage points.</p><p><strong>{report.interpretation === 'inconclusive-low-baseline' ? 'Inconclusive: the baseline recognizer was too weak.' : report.interpretation === 'reduced-recognition-in-this-test' ? 'Recognition decreased in this limited experiment.' : 'No recognition reduction demonstrated.'}</strong></p></>}
      <a className="primary" href={result} download={kind === 'cloak' ? 'viel-cloaked.png' : 'viel-proof.json'}>{kind === 'cloak' ? 'Download cloaked PNG' : 'Download measured report'}</a>
      {report && <details><summary>Experiment details</summary><pre className="json-report">{JSON.stringify(report, null, 2)}</pre></details>}
      <button className="text-button" onClick={() => { if (jobId.current) void fetch(`/api/face/jobs/${jobId.current}`, { method: 'DELETE' }); setResult(null); setReport(null); jobId.current = null; }}>Clear result</button>
    </div>{kind === 'cloak' && <img src={result} alt="Fawkes cloaked face photo"/>}</article>}
  </section>;
}
