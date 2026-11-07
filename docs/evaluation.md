# Evaluate the actual product claim

The goal has two independent parts: humans should see substantially the same image, and an AI editor should fail at the requested manipulation significantly more often than for the original. An encoder objective is only a proxy.

1. Use a consented set of diverse images, not only selected successes. Record exact model revision, software versions, source dimensions, profile, GPU, and runtime.
2. Generate a PNG candidate and preserve its JSON report. Inspect side-by-side at full size. Measure pixel differences and preferably perceptual similarity; ask blind human raters whether changes are visible. Do not choose a success threshold after seeing outcomes.
3. Apply the same benign edit prompts to both images, controlling model/version, settings, seed and masks where available. Repeat stochastic editors enough times to distinguish variability from a protection effect. Include unmodified re-encoded PNG controls and matched-budget random-noise controls.
4. Compare requested-edit success, semantic preservation, and artifact severity using predefined blind ratings. Image difference alone is not failure: different random seeds also change outputs.
5. Repeat after JPEG recompression, resizing, screenshots, and other expected upload transformations. Record every failure. Check that perceived protection persists beyond one hand-picked prompt.
6. For Meta AI, manually upload the original and candidate to the actual service if available. Record the date, interface, prompt, settings, any visible model information and returned images. There is no direct Meta AI integration here; do not infer its behavior from a Stable Diffusion test.

Report raw paired outputs alongside aggregates and confidence intervals. Generation failures, transparent-image rejections, and timeouts count as operational failures, not successful protection. No result currently supports the specific claim that edits become indecipherable on Meta AI. Recognition/OCR resistance is a different claim requiring different tests.
