# Face Cloak and measured recognition experiment

This flow targets Fawkes-style facial-recognition training privacy. It does not target Meta AI image editing. The original Stable Diffusion editor experiment is retained in source only; it did not establish Meta AI protection and is no longer the website's main flow.

## Start the service

Open `notebooks/viel_face_cloak.ipynb` in Colab. Run its two code cells. It installs the actual pinned upstream Fawkes in isolated Python 3.8, downloads its official encoder weights with upstream checksums, starts an authenticated API, and downloads connection configuration. No photos are uploaded through Colab cells.

Fawkes runs on CPU to avoid old TensorFlow/CUDA incompatibility. It can take several minutes per image. The host uses PyTorch/FaceNet for independent recognition. The setup checks an untrained encoder forward pass for runtime compatibility; that check is not efficacy evidence. The public weight downloads and legacy runtime can fail; setup must complete before claiming readiness.

Stop the website terminal with Ctrl+C. In Windows PowerShell:

```powershell
cd "$env:USERPROFILE\viel"
git pull --ff-only
npm.cmd ci
Move-Item "$env:USERPROFILE\Downloads\viel-backend.env" ".env.local" -Force
npm.cmd run dev -- --host 127.0.0.1
```

Open the printed URL and click Check Fawkes connection. Keep Colab and the local website server running. Configuration is private; do not share its token. A new Colab session needs a fresh configuration. This is a temporary development service.

## Generate a cloak

Select Cloak a face photo, choose a PNG/JPEG on the website, consent to processing, and generate. Check the original and cloaked photo side by side. A changed image alone does not prove training protection. A photo with no detectable face is an error, not a successful cloak. Higher modes may be more visible. The image must have sides from 32 to 1024 pixels, at most 10 MB, and be opaque.

## Prepare the proof ZIP

Use photos you have permission to process. Choose at least three different people. For each person provide at least three training photos and two genuinely different, clean test photos. More photos and identities improve the experiment. Avoid near-duplicates, screenshots of training photos, or identical images saved with different encodings.

| ZIP path example | Role |
|---|---|
| `train/person_a/1.jpg` | Training photo for person_a |
| `train/person_a/2.jpg` | Different training photo |
| `train/person_a/3.jpg` | Different training photo |
| `test/person_a/4.jpg` | Separate, previously unseen test photo |
| `test/person_a/5.jpg` | Separate, previously unseen test photo |

Repeat this layout for person_b and person_c. ZIP the train and test folders together, without an outer folder. Person labels must contain only letters, numbers, underscores, or hyphens. Use simple photo filenames. Limits: 3–10 identities, 60 photos, 64 MB ZIP/uncompressed image bytes. Every image must contain exactly one detectable face.

On the website select Run a recognition experiment, choose the ZIP, and enter the identity folder to protect, e.g. person_a. All image selection happens on the website. Wait for the asynchronous job; short polling avoids a long tunnel request.

## What the experiment actually does

1. Read and normalize the photos. Reject exact decoded duplicates, including across train/test. Near-duplicate detection is not implemented; prepare the split carefully.
2. Use a pretrained, frozen FaceNet InceptionResnetV1/vggface2 encoder and fit a logistic identity classifier on original training photos.
3. Run real upstream Fawkes on only the target person's training photos. Keep every test photo clean and unchanged.
4. Fit a second classifier with identical settings using the cloaked target training photos and unchanged other-person training photos.
5. Evaluate both classifiers on the exact same held-out clean photos. Report counts, accuracy change, predictions, dataset hashes, actual encoder-weight fingerprint, and software versions.

This is a limited transfer-learning classifier experiment, not a reproduction of the paper's full training evaluation. The evaluator's independent weights were not optimized against the uploaded cloak. Pretraining identity overlap is not audited; the underlying encoder may already know some identities. No images are used to fine-tune its backbone.

## Interpreting proof

If the baseline target recognition is below 80%, the result is inconclusive. If cloaked-training recognition is equal or higher, the UI says no reduction demonstrated. If it decreases, the report supports only that measured result for this dataset/encoder/classifier. With two target test photos a single changed prediction moves accuracy by 50 percentage points; it is not statistically strong evidence.

Upstream cloaking randomness is not seeded by this wrapper. Record several runs across independently selected datasets and encoders, report failures, and assess human-visible differences separately. The app does not currently compute uncertainty intervals or automatic human-similarity judgements. Do not claim universal protection, guaranteed invisibility, existing-model blindness, or Meta AI resistance.

## Data handling

Requests require a private bearer token injected by Vite's proxy. Images and ZIPs are sent to the configured service after explicit consent. The backend writes temporary files while Fawkes runs, deletes them when the job exits, and retains only the downloadable result/report in memory for up to 30 minutes or until deletion, capped at four records. Closing the tab does not guarantee job cancellation; use Cancel experiment. Downloaded files remain on your device. Colab/hosting infrastructure has its own retention behavior.
