"""Targeted projected gradient descent; no inference-mode context is permitted here."""
import threading
import torch


class Cancelled(Exception):
    pass


def optimize(image, encode, *, epsilon: float, steps: int, seed: int,
             cancel: threading.Event | None = None):
    if not 0 < epsilon <= 16 / 255 or not 1 <= steps <= 200:
        raise ValueError("Invalid optimization budget.")
    original = image.detach().clone()
    generator = torch.Generator(device=original.device).manual_seed(seed)
    candidate = (original + (torch.rand(original.shape, generator=generator,
                 device=original.device) * 2 - 1) * epsilon).clamp(0, 1)
    # Target a neutral-gray image's latent representation, rather than its pixels.
    with torch.no_grad():
        target = encode(torch.full_like(original, 0.5)).detach()
        initial = ((encode(original) - target) ** 2).mean().item()
    best, best_loss = original.clone(), initial
    step_size = epsilon / 4
    for iteration in range(steps):
        if cancel is not None and cancel.is_set():
            raise Cancelled("Experiment cancelled.")
        candidate = candidate.detach().requires_grad_(True)
        loss = ((encode(candidate) - target) ** 2).mean()
        if not torch.isfinite(loss):
            raise RuntimeError("Non-finite encoder objective.")
        if loss.item() < best_loss:
            best, best_loss = candidate.detach().clone(), loss.item()
        gradient, = torch.autograd.grad(loss, candidate)
        if not torch.isfinite(gradient).all():
            raise RuntimeError("Non-finite encoder gradient.")
        with torch.no_grad():
            rate = step_size * (1 - 0.9 * iteration / steps)
            candidate = candidate - rate * gradient.sign()
            candidate = torch.maximum(torch.minimum(candidate, original + epsilon), original - epsilon).clamp(0, 1)
    with torch.no_grad():
        final = ((encode(candidate) - target) ** 2).mean().item()
        if final < best_loss:
            best, best_loss = candidate.detach(), final
    return best, {"objective_before": initial, "objective_after": best_loss}
