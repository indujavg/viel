export type Health = { ready: boolean; busy: boolean; experimental: boolean };
export type Report = Record<string, string | number | null>;

export async function checkHealth(signal?: AbortSignal): Promise<Health> {
  const response = await fetch('/api/health', { signal, cache: 'no-store', credentials: 'same-origin' });
  if (!response.ok) throw new Error('Engine unavailable. Start the backend and check its credentials.');
  const data = await response.json();
  if (typeof data.ready !== 'boolean' || data.experimental !== true) throw new Error('Unexpected engine response.');
  return data;
}

export async function protectImage(file: File, profile: string, signal: AbortSignal): Promise<{ blob: Blob; report: Report }> {
  const response = await fetch(`/api/protect?profile=${encodeURIComponent(profile)}&seed=42`, {
    method: 'POST', body: file, headers: { 'Content-Type': file.type }, signal, credentials: 'same-origin',
  });
  if (!response.ok) {
    const error = await response.json().catch(() => null);
    throw new Error(error?.error?.message || `Experiment failed (${response.status}).`);
  }
  if (!response.headers.get('content-type')?.startsWith('image/png')) throw new Error('The engine did not return a PNG image.');
  const report = JSON.parse(response.headers.get('X-Viel-Report') || 'null');
  if (!report || report.status !== 'experimental-unverified') throw new Error('Missing experimental result metadata.');
  const blob = await response.blob();
  if (!blob.size || blob.size > 10 * 1024 * 1024) throw new Error('The result has an invalid size.');
  return { blob, report };
}
