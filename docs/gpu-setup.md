# Run the experimental engine

There is no hosted backend URL yet. Choose local GPU execution or the notebook. GPU memory/runtime needs have not been benchmarked; begin with a 256×256 image and the Subtle profile.

## Local computer or private GPU server

Use Python 3.12 and a CUDA-capable NVIDIA GPU with suitable drivers. From the repository root:

```sh
python -m venv .venv
# macOS/Linux shell:
source .venv/bin/activate
# Windows PowerShell instead: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Install CUDA-enabled PyTorch using the command selected for your system at https://pytorch.org/get-started/locally/ . CPU-only PyTorch will not enable the service. Then:

```sh
pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
cp .env.example .env.local
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the generated secret into `VIEL_API_TOKEN` in both private files. Do not paste it into chat, GitHub, or browser code. On Windows, use `Copy-Item` in place of `cp` if needed.

Review the model card/license at https://huggingface.co/stabilityai/sd-vae-ft-mse . Obtain the exact current model commit SHA, then copy it into `VIEL_MODEL_REVISION` in `backend/.env`:

```sh
python -c "from huggingface_hub import model_info; print(model_info('stabilityai/sd-vae-ft-mse').sha)"
```

Pinning this SHA makes the model revision explicit; it does not certify model quality or licensing. Model weights download on first startup, so internet access is required then. Start the API:

```sh
uvicorn backend.app:app --env-file backend/.env --host 127.0.0.1 --port 8000 --workers 1
```

In a second terminal, run `npm run dev`. Restart Vite after changing `.env.local`. Check connection in the website. Select a small opaque image, consent to processing, and generate a candidate. If startup fails, health stays unavailable and the API logs the reason. Download both PNG and experiment record, then follow `docs/evaluation.md`.

## Colab alternative

Open `notebooks/viel_gpu_experiment.ipynb` in Google Colab, select a GPU runtime, and run its cells. GPU availability and charges depend on your account; the notebook does not provision paid resources. It runs the same optimizer and lets you download a PNG plus JSON report. It does not create a permanent API URL or connect the website automatically.

## Public website deployment

The frontend builds into `dist/`; the optimizer needs a separate persistent GPU process. A public deployment needs a chosen hosting account, an HTTPS domain, and an authenticated/rate-limited same-origin gateway. Never put the GPU token in a static-host build variable named `VITE_*`. The current repository provides the runnable components, not a public deployment or subscription.
