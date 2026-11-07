"""Experimental PhotoGuard-inspired encoder baseline, not a verified defense."""
import os
import time
import hashlib
import threading
import numpy as np
from PIL import Image
from .images import pixel_metrics, png_bytes

PROFILES = {"subtle": {"budget": 4, "steps": 80}, "balanced": {"budget": 8, "steps": 120}}


class ShieldEngine:
    def __init__(self):
        import torch
        from diffusers import AutoencoderKL
        if not torch.cuda.is_available():
            raise RuntimeError("A CUDA GPU is required for the experimental engine.")
        self.model_id = os.environ.get("VIEL_MODEL_ID", "stabilityai/sd-vae-ft-mse")
        self.revision = os.environ.get("VIEL_MODEL_REVISION")
        if not self.revision or len(self.revision) != 40 or any(c not in '0123456789abcdef' for c in self.revision):
            raise RuntimeError("Set VIEL_MODEL_REVISION to the reviewed model's 40-character commit SHA.")
        self.vae = AutoencoderKL.from_pretrained(self.model_id, revision=self.revision,
                    torch_dtype=torch.float32, use_safetensors=True).to("cuda").eval()
        self.vae.requires_grad_(False)

    def protect(self, image: Image.Image, profile: str, seed: int, cancel: threading.Event):
        import torch
        import torch.nn.functional as F
        from .optimizer import optimize
        started = time.monotonic()
        config = PROFILES[profile]
        source = np.asarray(image, dtype=np.uint8).copy()
        x = torch.from_numpy(source).permute(2, 0, 1).unsqueeze(0).to("cuda", dtype=torch.float32) / 255
        h, w = source.shape[:2]
        def encode(value):
            # Padding only; never silently resize or crop the user's photo.
            padded = F.pad(value, (0, (-w) % 8, 0, (-h) % 8), mode="replicate")
            return self.vae.encode(padded * 2 - 1).latent_dist.mean
        candidate, objective = optimize(x, encode, epsilon=config['budget']/255,
                            steps=config['steps'], seed=seed, cancel=cancel)
        if cancel.is_set():
            from .optimizer import Cancelled
            raise Cancelled()
        array = candidate[0].detach().cpu().permute(1, 2, 0).numpy()
        exported = np.rint(array * 255).astype(np.int16)
        original = source.astype(np.int16)
        exported = np.clip(exported, original-config['budget'], original+config['budget']).clip(0,255).astype(np.uint8)
        result = Image.fromarray(exported)
        if image.info.get("icc_profile"):
            result.info["icc_profile"] = image.info["icc_profile"]
        metrics = pixel_metrics(image, result)
        if metrics['max_channel_change'] == 0 or objective['objective_after'] >= objective['objective_before']:
            raise RuntimeError("No useful candidate was found; no result will be returned.")
        with torch.no_grad():
            quantized = torch.from_numpy(exported.copy()).permute(2,0,1).unsqueeze(0).to('cuda',dtype=torch.float32)/255
            target = encode(torch.full_like(x, 0.5))
            exported_objective = ((encode(quantized)-target)**2).mean().item()
        if not np.isfinite(exported_objective) or exported_objective >= objective['objective_before']:
            raise RuntimeError("The exported candidate did not improve the encoder objective.")
        output = png_bytes(result)
        report = {"method": "targeted-vae-pgd-v1", "status": "experimental-unverified",
            "model": self.model_id, "revision": self.revision, "profile": profile,
            "seed": seed, "steps": config['steps'], "budget_8bit": config['budget'],
            "width": w, "height": h, "runtime_seconds": round(time.monotonic()-started,2),
            "output_sha256": hashlib.sha256(output).hexdigest(),
            "decoded_input_sha256": hashlib.sha256(source.tobytes()).hexdigest(),
            "device": torch.cuda.get_device_name(), "torch_version": torch.__version__,
            "objective_exported": exported_objective, **objective, **metrics}
        return output, report
