# viel

An experimental image-shielding website: preserve the appearance of photos while researching pixel changes that disrupt AI editing.

## What is implemented

- React + TypeScript + Vite interface with local preview and a manual comparison lab.
- Explicit consent before sending an image to the configured service.
- Python/FastAPI `/health` and `/protect` service with bearer authentication, input limits, one active GPU request, cancellation, and in-memory processing.
- A PhotoGuard-inspired targeted encoder optimizer: projected gradient descent against a frozen Stable Diffusion VAE, targeting a neutral-gray image's latent representation.
- Lossless candidate PNG download and a JSON experiment report, including pixel-change metrics and model revision.
- A Colab notebook for standalone GPU experiments.

**This is experimental software, not verified protection.** The engine has not been evaluated on real image-editing outputs. Meta AI effectiveness is unknown. A lower encoder objective and small pixel differences do not prove editing disruption. The engine does not make images universally unreadable to AI.

## Website setup (beginner friendly)

Install Git and Node.js 24 (npm is included). In a terminal:

```sh
git clone --branch setup/viel-foundation https://github.com/indujavg/viel.git
cd viel
npm ci
npm run dev
```

Open the URL printed by Vite. The website works for local previews without a backend. The engine status remains offline and candidate generation stays disabled until the backend is ready.

Edit `src/App.tsx` for the page, `src/ShieldWorkspace.tsx` for the shielding flow, and `src/styles.css` for styling. Save a file to see changes in the browser. Ctrl+C stops the local server.

```sh
npm test                 # validation tests
npm run check            # TypeScript checks
npm run build            # checks types and builds dist/
npm run preview          # views the built frontend; no API proxy
npx playwright install chromium
npm run test:e2e          # browser tests; API responses are synthetic test fixtures
```

`package-lock.json` records the resolved frontend dependencies. Use `npm ci` for repeatable installs; use `npm install` only when deliberately changing dependencies and commit the updated lockfile. GitHub Actions runs the production build, browser tests, and CPU backend tests.

## Enable the real experimental engine

See [GPU setup](docs/gpu-setup.md). It requires Python 3.12, a CUDA GPU, PyTorch, and a reviewed/pinned model download. No GPU service is deployed by this repository.

The supplied engine accepts **opaque RGB/grayscale PNG or JPEG, 10 MB maximum, 32–1024 pixels per side**. Larger pictures must be resized explicitly before processing. It keeps oriented dimensions unchanged and strips metadata when exporting PNG. Subtle permits at most 4/255 per RGB channel; Balanced permits 8/255. These bounds do not guarantee imperceptibility.

## Structure

| Path | Responsibility |
|---|---|
| `src/` | Website and API client |
| `backend/` | API, image validation, GPU optimizer |
| `tests/`, `e2e/`, `backend/tests/` | Input, browser, API, and mathematical optimizer tests |
| `notebooks/` | Standalone Colab experiment |
| `docs/` | Requirements, setup, API contract, evaluation protocol |
| `.github/workflows/ci.yml` | Frontend build/browser tests and CPU backend tests |

## Privacy and deployment

Selecting images only previews them locally. Clicking Generate after consent sends the original to the configured backend. The supplied backend uses memory, with no image files or experiment records written to disk. Hosting infrastructure may have its own retention/logging. Refreshing clears browser state; downloads are saved by the user.

Vite's development proxy reads `VIEL_API_TOKEN` server-side; never prefix a secret with `VITE_`. Keep `.env.local` and `backend/.env` private. The dev server binds to loopback. For public deployment, serve `dist/` over HTTPS and put `/api/*` behind an authenticated, rate-limited gateway which injects the backend token server-side. An ordinary static host alone cannot run this GPU engine. Do not expose the private GPU API or token to visitors.

## Evidence and next milestone

Run a real GPU experiment, inspect perceptual quality, then compare multiple matched edits of original/candidate photos. See [evaluation](docs/evaluation.md). No API unit test, mocked browser test, or optimizer toy test is evidence of real-model protection.

Research references: [PhotoGuard](https://github.com/MadryLab/photoguard), [paper](https://arxiv.org/abs/2302.06588), [DiffusionGuard](https://arxiv.org/abs/2410.05694). The optimizer is an independent experimental implementation inspired by targeted encoder attacks; it is not an official reproduction or a full diffusion attack. Review model licenses separately before use.
