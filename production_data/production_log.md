# Production log

Newest first. One entry per production run or system change. The machine-readable record is `production_registry.json`.

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
