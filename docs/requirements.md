# Requirements and milestones

## Confirmed goal

A website where users shield pictures with subtle changes: the image should look substantially the same to humans while edits produced by an AI editor are severely disrupted compared with edits of the original. Meta AI is an intended evaluation target, not a supported or proven integration. Stack: React, TypeScript, Vite.

## Milestone 1: reviewable frontend foundation

- Local PNG/JPEG selection and preview; maximum 10 MB and 24 megapixels.
- Reject invalid input and failed image decoding.
- Independently select original, candidate shielded image, and two edited outputs.
- Responsive layout, labelled controls, visible keyboard focus, reduced-motion support.
- No image upload, persistence, synthetic results, or claims of proven protection.
- Shield action disabled until a real engine and its validation are available.
- Validation tests, type check, and production build must pass before calling the milestone fully validated.

## Milestone 2: one reproducible engine experiment

Choose an accessible image-editing model, review licenses and GPU needs, and reproduce a documented protection technique against that model. Implement and measure a real optimizer; random noise and visible watermarks do not satisfy the goal. Preserve output as lossless PNG. Record model revision, method, perturbation budget, seed, preprocessing, runtime, and hardware. Provide a reproducible notebook or Python service only after this experiment is specified.

## Milestone 3: evidence and backend integration

Use multiple consented images, prompts, and repeated runs. Compare original and candidate perceptual quality, plus edits of both under matched settings. Include resizing, compression, and screenshot conditions. Report both failures and successes; define thresholds before testing. Visible output differences may come from randomness, so one screenshot comparison is insufficient. Measure human similarity separately from edit disruption. Successful editing disruption does not prove the image is unreadable to recognition models.

Meta AI testing, if available to the user, starts with manually exported outputs and recorded date/settings. No direct integration is assumed. Do not generalize performance across model families or future versions.

## Deferred

Accounts, payments, database storage, automatic Meta AI access, deployment, and universal protection claims. A future backend needs explicit upload consent, retention/deletion behavior, authentication, rate limits, resource limits, and cancellation before public use.
