# Requirements and status

## Confirmed purpose

Users want pictures that look substantially the same to people but cause AI edits to diverge severely from successful edits of unprotected originals. Meta AI is an intended evaluation target. Stack: React + TypeScript + Vite, with a Python GPU service for optimization.

## Implemented for development

- Responsive blue website with local previews and manual paired-output comparison.
- Explicit upload consent, backend readiness, two bounded profiles, cancellation, PNG and report downloads.
- FastAPI service with authentication and decoded input validation.
- Real gradient-based VAE encoder optimizer; exact model revision required; no unmodified-image fallback.
- Unit/API/browser tests and a GPU notebook.

## Not established

- Human imperceptibility at either pixel budget.
- Disruption of a real image editor, including Meta AI.
- Robustness to uploads, compression, resizing, screenshots, or future editors.
- Production GPU memory/runtime requirements, public hosting, or access control for end users.

## Acceptance gates

Software gate: unit, API, browser, type, and production-build checks pass. These checks can use test fixtures but must identify them as such.

Engine gate: actual model loads on a GPU; exported PNG obeys the budget and reduces the intended encoder objective. This remains unverified until run with real weights.

Product gate: matched editing experiments show meaningful disruption while blind human assessment confirms acceptable visual similarity. See `evaluation.md`. Do not present a candidate-generation success as this gate passing.
