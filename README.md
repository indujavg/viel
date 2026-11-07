# viel

An experimental website for image shielding: preserve the appearance of a photo while exploring model-specific perturbations that disrupt AI editing.

## Current milestone

React + TypeScript + Vite frontend with local PNG/JPEG selection, decoded-image validation, original preview, and a manual comparison lab. Responsive blue visual design and keyboard-accessible controls.

**No shielding engine is implemented or connected.** The Shield button is disabled. No protective image, watermark, random-noise substitute, AI edit, or protection score is generated. Meta AI effectiveness is untested. Comparison images are supplied by the user and are not verified.

Images are held in browser memory, not sent to a server or saved by this app. Refreshing clears the session. Do not use this prototype as a proven safeguard.

## Run on your computer

Install Git and Node.js 24 (which includes npm). After the proposed files are approved and merged:

```sh
git clone https://github.com/indujavg/viel.git
cd viel
npm install
npm run dev
```

Open the local URL printed by Vite. Edit `src/App.tsx` for the interface and `src/styles.css` for styling; the development server updates your browser as you save. Press Ctrl+C in the terminal to stop it.

```sh
npm test          # input-validation tests
npm run check    # TypeScript checks
npm run build    # checks types and writes deployable files into dist/
npm run preview  # view the built site locally
```

The initial draft has no package lock because the preparation environment blocks npm downloads. On the first successful `npm install`, review and commit `package-lock.json`, then switch CI to `npm ci`. Thereafter use `npm ci` for reproducible installs. Declared dependency ranges have not been installation-tested here.

## Layout

- `src/App.tsx`: image-selection cards and comparison workspace.
- `src/lib/image.ts`: file and dimension limits.
- `src/styles.css`: responsive visual design.
- `tests/`: validation tests using Node's built-in test runner.
- `docs/requirements.md`: goals, acceptance criteria, and research roadmap.
- `docs/backend-contract.md`: proposed future engine contract; no service exists yet.
- `.github/workflows/ci.yml`: tests and build for proposed changes.

## Manual checks

Select a valid PNG and JPEG; preview each. Try a wrong type, empty file, corrupt image, a file over 10 MB, and an image over 24 megapixels. Check errors, removal, rapid replacement, all four image slots, keyboard focus, and a 375px-wide screen. Confirm Shield remains disabled and image selection creates no network upload.

## Development workflow

Make changes on a branch and open a pull request (a reviewable proposal) before merging into `main`. Initial publication requires the owner's explicit approval. Do not commit private photos, credentials, model weights, or generated build files. A future backend must keep credentials server-side; browser environment variables are public.

## Research basis

- PhotoGuard: https://github.com/MadryLab/photoguard
- Paper: https://arxiv.org/abs/2302.06588
- DiffusionGuard: https://arxiv.org/abs/2410.05694

These are research references, not bundled engines or evidence of protection against Meta AI. Review model/code licenses and hardware requirements before integrating an implementation.
