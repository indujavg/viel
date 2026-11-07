# viel — Face Cloak

A website integrating actual upstream Fawkes to explore privacy against facial-recognition training. Photos are selected on the website; Colab runs the service. This does not protect against Meta AI editing.

## Run the website on Windows

```powershell
git clone https://github.com/indujavg/viel.git
cd viel
npm.cmd ci
npm.cmd run dev -- --host 127.0.0.1
```

If already cloned, stop the dev server and run `git pull --ff-only`, then `npm.cmd ci` and restart it. Open the Local URL printed by Vite. Keep the terminal open.

## Connect Fawkes and run a measured experiment

Open [the Face Cloak notebook](https://colab.research.google.com/github/indujavg/viel/blob/main/notebooks/viel_face_cloak.ipynb). Run its setup and service cells, then install its downloaded connection configuration as described in [face-proof.md](docs/face-proof.md). There are no photo-upload cells. Fawkes uses an isolated CPU runtime, so a GPU is not required.

The website offers a single-photo cloak and a recognition experiment. The latter compares classifiers fitted using original vs. cloaked training photos, evaluated on identical clean held-out photos. It requires a labelled train/test ZIP with at least 3 identities, 3 training photos and 2 separate test photos per identity. See the full layout and limitations in [face-proof.md](docs/face-proof.md).

**Current evidence:** integration tests are separate from actual protection measurements. A generated cloak, model-weight download, or a successful smoke test does not prove training protection. The website displays actual experiment counts and includes failure/inconclusive outcomes; no successful face-recognition result is bundled or claimed.

## Development

Node 24, React, TypeScript, Vite. `npm ci` uses the committed lockfile.

```sh
npm test
npm run check
npm run build
npx playwright install chromium
npm run test:e2e
```

Backend: `backend/face_app.py` provides authenticated asynchronous jobs. `backend/faces/` contains upstream Fawkes execution, dataset validation and a limited independent recognition evaluator. `scripts/setup_face_colab.py` builds isolated dependencies. Old Stable Diffusion experiment files remain available for research history; that method failed the user's Meta AI test and is not used by the Face Cloak interface.

The Fawkes code pins TensorFlow 2.4.1 and requires a separate legacy Python environment; installing it into the main Colab Python will not work. CPU-based setup avoids legacy CUDA compatibility. The notebook validates installation and model checksums, but upstream hosting and runtime compatibility may still fail. Software test fixtures are not efficacy evidence.

For private development only: keep tokens in ignored environment files, bind local services to loopback, and use the authenticated tunnel from the notebook. Production deployment needs managed hosting, end-user authentication, rate limits and retention controls. Fawkes writes temporary images while running; they are deleted when a job ends. Results expire after 30 minutes.

See [third-party notices](THIRD_PARTY_NOTICES.md) for attribution and licences.
