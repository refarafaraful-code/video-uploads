# Production log

Newest first. One entry per production run or system change. The machine-readable record is `production_registry.json`.

## 2026-10-24 — audit of the production system (no clips produced, nothing published)
- Found and fixed: trimmed/re-encoded copies of a processed source were classified `new` (hash/duration only).
  Added chromaprint audio fingerprints (windowed alignment) + own-clip hash check; stored fingerprints for both
  sources (`production_data/fingerprints/`, additive registry change). Duplicate suite: 11/11 pass.
- Added `registry.py register-source` (refuses duplicates), session-only file notes in `verify`.
- `qc.py`: black/frozen/silent stretches and duplicate outputs now give `needs_review` (were warnings); 9 synthetic
  defect cases behave as expected; all 14 real files pass.
- `make_clip.py`: refuses to overwrite an existing output (tested).
- Publishing: default changed to per-batch confirmation (CLIPPINGMASTER §14); `.claude/settings.json` adds an
  approval prompt for Metricool scheduling tools. Existing 5 scheduled posts untouched.
- `CLAUDE.md` now imports `CLIPPINGMASTER.md` with `@` (verified against Claude Code docs; not yet observed in a
  fresh session).

## 2026-10-24 — system setup (no clips produced)
- Saved the owner's standing instructions to `production_data/CLIPPINGMASTER.md` and linked them from `CLAUDE.md`.
- Created `production_registry.json` (atomic writes via `clipper/registry.py`), `clipper/qc.py` (automated technical QC).
- Backfilled the two historical runs below from release-asset digests, local renders, specs and Metricool.
- Automated QC run on all 9 historical renders and the 5 publish copies: all pass
  (01_mini_lambo_reveal: note, 62.6 s > 60 s).
- Verified both sources' sha256 equal the GitHub release asset digests.
- Known gaps: master renders of all 9 clips exist only in the (ephemeral) session and in the chat with the owner;
  only the 5 publish copies are in the repo. The 4 mini-lambo clips were uploaded by the owner by hand — titles used
  and upload status are unverified. Historical candidates were not numerically scored.

## 2026-10-23 — run-2026-10-23-b: "MY BROTHER KIDNAPPED MY WIFE" (src-kidnapped-wife)
- 5 clips (pipeline v2), delivered in chat; publish copies in `shorts-v2/`; scheduled in Metricool 24–28 Oct, 15:00 New York.

## 2026-10-23 — run-2026-10-23-a: "SURPRISING MINI JAKE PAUL WITH A MINI LAMBORGHINI" (src-mini-lambo)
- 4 clips (pipeline v1), delivered in chat; owner uploaded them to YouTube manually.
