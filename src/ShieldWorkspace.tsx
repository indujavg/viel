import { useEffect, useRef, useState } from 'react';
import { checkHealth, protectImage } from './lib/api';
import type { Health, Report } from './lib/api';
import { validateFile } from './lib/image';

type Source = { file: File; url: string; width: number; height: number };
type Candidate = { url: string; report: Report; reportUrl: string };

export function ShieldWorkspace() {
  const [source, setSource] = useState<Source | null>(null);
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [connection, setConnection] = useState('Checking engine…');
  const [profile, setProfile] = useState('subtle');
  const [consent, setConsent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [reading, setReading] = useState(false);
  const [error, setError] = useState('');
  const version = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const healthController = useRef<AbortController | null>(null);
  const picker = useRef<HTMLInputElement>(null);

  async function refreshHealth() {
    healthController.current?.abort();
    const abort = new AbortController();
    healthController.current = abort;
    const timer = window.setTimeout(() => abort.abort(), 8000);
    setConnection('Checking engine…');
    try {
      const state = await checkHealth(abort.signal);
      if (healthController.current !== abort) return;
      setHealth(state);
      setConnection(state.ready ? (state.busy ? 'Engine busy — retry shortly' : 'Experimental engine connected') : 'Engine offline — check GPU and model setup');
    } catch {
      if (healthController.current !== abort) return;
      setHealth(null); setConnection('Engine offline — start the service to generate a candidate');
    } finally { window.clearTimeout(timer); }
  }
  useEffect(() => { void refreshHealth(); return () => { ++version.current; controller.current?.abort(); healthController.current?.abort(); }; }, []);
  useEffect(() => () => { if (source) URL.revokeObjectURL(source.url); }, [source]);
  useEffect(() => () => { if (candidate) { URL.revokeObjectURL(candidate.url); URL.revokeObjectURL(candidate.reportUrl); } }, [candidate]);

  async function select(file: File | undefined) {
    if (!file) return;
    const current = ++version.current;
    controller.current?.abort();
    setBusy(false); setCandidate(null); setSource(null); setConsent(false); setError('');
    const invalid = validateFile(file);
    if (invalid) { setError(invalid); setReading(false); return; }
    setReading(true);
    const url = URL.createObjectURL(file);
    try {
      const image = new Image(); image.src = url; await image.decode();
      if (version.current !== current) { URL.revokeObjectURL(url); return; }
      if (Math.min(image.naturalWidth, image.naturalHeight) < 32 || Math.max(image.naturalWidth, image.naturalHeight) > 1024) throw new Error('Use an image with each side between 32 and 1024 pixels. Resize a copy first.');
      setSource({ file, url, width: image.naturalWidth, height: image.naturalHeight });
    } catch (reason) {
      URL.revokeObjectURL(url);
      if (version.current === current) setError(reason instanceof Error && reason.message.startsWith('Use') ? reason.message : 'This image could not be decoded. Choose another PNG or JPEG.');
    } finally { if (version.current === current) setReading(false); }
  }

  async function shield() {
    if (!source || !consent || busy || !health?.ready) return;
    const current = ++version.current;
    const abort = new AbortController(); controller.current = abort;
    setBusy(true); setCandidate(null); setError('');
    const timer = window.setTimeout(() => abort.abort(), 250000);
    let url: string | null = null;
    try {
      const result = await protectImage(source.file, profile, abort.signal);
      if (current !== version.current) return;
      url = URL.createObjectURL(result.blob);
      const image = new Image(); image.src = url; await image.decode();
      if (current !== version.current) { URL.revokeObjectURL(url); return; }
      if (image.naturalWidth !== source.width || image.naturalHeight !== source.height) throw new Error('The service changed image dimensions. Result rejected.');
      const reportUrl = URL.createObjectURL(new Blob([JSON.stringify(result.report, null, 2)], { type: 'application/json' }));
      setCandidate({ url, report: result.report, reportUrl });
      url = null;
    } catch (reason) {
      if (url) URL.revokeObjectURL(url);
      if (current === version.current) setError(abort.signal.aborted ? 'Request cancelled or timed out. No new candidate is available.' : reason instanceof Error ? reason.message : 'The experiment failed.');
    } finally {
      window.clearTimeout(timer);
      if (current === version.current) setBusy(false);
    }
  }

  return <div className="shield-workspace">
    <div className="workspace-grid">
      <article className="image-card">
        <h3>Original photo</h3><p id="source-help">Opaque PNG or JPEG · 10 MB maximum · 32–1024 pixels per side</p>
        <div className="preview">{source ? <img src={source.url} alt="Original selected photo"/> : <span>{reading ? 'Reading image…' : 'Your image goes here'}</span>}</div>
        <label htmlFor="shield-source" className="file-label">Choose your original</label>
        <input ref={picker} id="shield-source" type="file" accept="image/png,image/jpeg" aria-describedby="source-help shield-error" onChange={e => { void select(e.target.files?.[0]); e.target.value = ''; }} />
        {source && <><p className="metadata">{source.file.name} · {source.width} × {source.height}</p><button className="text-button" onClick={() => { ++version.current; controller.current?.abort(); setBusy(false); setSource(null); setCandidate(null); setConsent(false); setError(''); picker.current?.focus(); }}>Remove original</button></>}
      </article>
      <aside className="engine-card">
        <span className="eyebrow">EXPERIMENTAL SHIELD ENGINE</span><h3>Small changes.<br/>A measurable experiment.</h3>
        <p role="status">{connection}</p><button className="text-button" onClick={() => void refreshHealth()} disabled={busy}>Check connection</button>
        <label className="file-label" htmlFor="profile">Pixel-change budget</label>
        <select id="profile" value={profile} disabled={busy} onChange={e => { setProfile(e.target.value); setCandidate(null); }}><option value="subtle">Subtle · up to 4 / 255 per channel</option><option value="balanced">Balanced · up to 8 / 255 per channel</option></select>
        <p className="fine-print">A larger budget permits more visible changes. Neither profile has proven effectiveness against Meta AI.</p>
        <label className="consent"><input type="checkbox" checked={consent} disabled={busy} onChange={e => setConsent(e.target.checked)}/> I agree to send this image to this site's configured shielding service for processing. The supplied backend processes it in memory.</label>
        <button className="primary" onClick={() => void shield()} disabled={!source || !consent || !health?.ready || health.busy || busy || reading}>{busy ? 'Calculating pixel changes…' : 'Generate shield candidate'}</button>
        {busy && <button className="text-button cancel" onClick={() => controller.current?.abort()}>Cancel experiment</button>}
        <p id="shield-error" role="alert" className="error">{error}</p>
        <p className="fine-print">Targets a Stable Diffusion encoder. A candidate is not a guarantee of protection.</p>
      </aside>
    </div>
    {candidate && <article className="result-card">
      <div><span className="eyebrow">EXPERIMENTAL RESULT</span><h3>Your candidate is ready to test.</h3><p>Compare it with the original, then test both in the same AI editor. Keep the PNG intact; conversion may weaken the perturbation.</p>
        <p>Maximum channel change: <strong>{String(candidate.report.max_channel_change)} / 255</strong></p>
        <a className="primary" href={candidate.url} download="viel-candidate.png">Download candidate PNG</a>{' '}<a className="report-link" href={candidate.reportUrl} download="viel-experiment.json">Download experiment record</a>
      </div><img src={candidate.url} alt="Experimental shield candidate"/>
    </article>}
  </div>;
}
