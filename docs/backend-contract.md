# Proposed protection API — design only

No backend is shipped. The frontend currently makes no API calls. Finalize this contract with the selected engine before implementation.

For a first, bounded experiment, propose `POST /protect` with multipart form data containing one `image` (PNG/JPEG), a server-approved `profile`, and numeric `seed`. The server validates actual decoded format, byte size, dimensions, and permitted profiles independently of browser checks. Do not accept arbitrary model paths or code from the client.

Success: `200 image/png`, a lossless candidate result. Include an experiment identifier in `X-Viel-Experiment-Id` and expose it through CORS if cross-origin. Record method/model revision, perturbation budget, input/output hashes, seed, runtime, and preprocessing in an experiment record. Candidate generation is not evidence of effectiveness.

Errors: structured JSON `{ "error": { "code": "...", "message": "..." } }` with statuses 400 (bad request), 413 (size), 415 (format), 422 (decode/profile), 429 (capacity), and 503 (engine unavailable). Never return the original as a successful protection result on failure. Long GPU jobs will need a separate queued-job API rather than an indefinite HTTP request.

Before wiring the frontend: agree on hosting, HTTPS, allowed origins, auth, timeouts/cancellation, retention/deletion, and model licensing. Show the service destination and obtain image-upload consent. Never store API secrets in Vite environment variables. Add an example environment file only when an actual endpoint configuration is implemented.
