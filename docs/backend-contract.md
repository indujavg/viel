# Implemented development API

The website calls same-origin `/api/health` and `/api/protect`. Vite strips `/api` and forwards to the configured GPU service, adding a secret bearer token server-side. Production needs an equivalent authenticated gateway; `vite preview` does not provide this proxy.

## Authentication

Every backend request requires `Authorization: Bearer <VIEL_API_TOKEN>`. Startup requires a secret of at least 32 characters. No browser API token is shipped. The API does not enable cross-origin access; the gateway handles same-origin routing.

## GET /health

Returns `{ "ready": true, "busy": false, "experimental": true, "method": "targeted-vae-pgd-v1", "profiles": ["subtle", "balanced"], "max_side": 1024 }`. `ready` is false when CUDA or model loading failed. Readiness means the engine loaded, not proven efficacy.

## POST /protect?profile=subtle&seed=42

Body is the raw PNG/JPEG bytes, with matching `Content-Type`. This supersedes the earlier proposed multipart contract. Limit: 10 MB; sides 32–1024 pixels; opaque RGB or grayscale; single frame. The service checks decoded format and dimensions. No resizing or cropping is performed. EXIF orientation is applied; metadata is removed from output.

Success is a lossless `image/png` with `Content-Disposition` and `X-Viel-Report` JSON. Report includes method, exact model revision, profile, random seed, budget, step count, runtime, input/output hashes, hardware, encoder objectives, and pixel metrics. Status is always `experimental-unverified`. An unchanged image or failed optimization is an error.

Statuses: 401 credentials, 413 oversized bytes, 415 unsupported Content-Type, 422 invalid image/settings, 429 GPU busy, 500 experiment failure, 503 engine unavailable, 504 four-minute deadline. Errors generally use `{ "error": { "code": "...", "message": "..." } }`; FastAPI's query type validation may use its standard `detail` envelope. Responses use `Cache-Control: no-store`.

One request runs per process. Use one Uvicorn worker per GPU. Disconnects/deadlines set a cancellation event checked between optimization steps; a currently executing GPU operation is not forcibly interrupted. The slot stays occupied until the worker stops. This development service has no persistent queue or public-user rate limiting. Put public deployments behind authenticated, rate-limited infrastructure with request body and upload time limits.
