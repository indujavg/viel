"""Decode bounded image inputs and measure exported PNGs without model dependencies."""
from io import BytesIO
import math
import warnings
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_BYTES = 10 * 1024 * 1024
MAX_SIDE = 1024


def decode_image(data: bytes) -> Image.Image:
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Choose a nonempty image up to 10 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as source:
                if source.format not in ("PNG", "JPEG"):
                    raise ValueError("Only PNG and JPEG are supported.")
                if getattr(source, "n_frames", 1) != 1:
                    raise ValueError("Animated images are not supported.")
                if min(source.size) < 32 or max(source.size) > MAX_SIDE:
                    raise ValueError("The experimental engine accepts sides from 32 to 1024 pixels. Resize a copy first.")
                if source.mode not in ("RGB", "L") or "transparency" in source.info:
                    raise ValueError("Use an opaque RGB or grayscale image; transparent and palette images are not supported by this engine.")
                source.load()
                return ImageOps.exif_transpose(source).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError, Image.DecompressionBombWarning) as error:
        raise ValueError("This file is not a supported, readable image.") from error


def png_bytes(image: Image.Image) -> bytes:
    stream = BytesIO()
    image.save(stream, format="PNG")
    return stream.getvalue()


def pixel_metrics(original: Image.Image, candidate: Image.Image) -> dict:
    if original.size != candidate.size:
        raise ValueError("Candidate dimensions must match the original.")
    delta = np.asarray(candidate, dtype=np.float32) - np.asarray(original, dtype=np.float32)
    mse = float(np.mean(delta ** 2))
    return {"max_channel_change": int(np.abs(delta).max()),
            "mean_absolute_change": round(float(np.abs(delta).mean()), 4),
            "psnr_db": round(10 * math.log10(255 ** 2 / mse), 3) if mse > 0 else None}
