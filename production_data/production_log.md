# Production log

Newest first. One entry per production run or system change. The machine-readable record is `production_registry.json`.

## 2026-10-24 — run-2026-10-24-general-matter (src-general-matter, release factory) — scheduled
- Eligibility: digest pre-screen `new`; 1 GB download resumed after a dropped connection, sha256 = GitHub digest;
  `registry.py check` `new`. 4K 6:46 documentary (Jake Paul / Anti Fund at General Matter, Paducah KY).
- 10 candidates: 4 selected (87, 84, 80, 78), 1 merged into another clip, 5 rejected.
- Full-frame 16:9 layout (kinetic text/charts span the frame width). 3 drafts rejected in editorial review (slow
  hook, missing final word, caption wider than frame) although technical QC passed them.
- Scheduled: 2 on Oct 24 (15:00 / 19:00 New York), 2 on Oct 25 (15:00 / 19:00 New York), Metricool, public Shorts.
- Earlier the same day: the owner had all 5 kidnapped-wife posts cancelled (now private drafts); standing
  authorization recorded and the Metricool approval rule removed at the owner's request.

## 2026-10-24 — run-test-1-snack-wars: controlled test (src-snack-wars, release v3) — nothing published
- Eligibility: digest pre-screen `new`; downloaded file sha256 = GitHub digest; `registry.py check` `new` (no hash,
  fingerprint or metadata match). Registered; filename bug in `register-source` found and fixed (`--filename`).
- Analysis: full transcript + 1 frame/5 s over all 11:01 + 1 fps sheets of candidate sections. 10 candidates scored:
  4 selected (88, 85, 78, 78), 6 rejected (69 and below).
- Renders: 4 final clips in `output/test-run-1-snack-wars/clips/`; 5 drafts rejected in editorial review although
  technical QC passed them (cut endings, emojis over a face, stray caption, undetected cuts); 1 render truncated by a
  container restart (caught by QC). Drafts kept on disk, git-ignored, recorded in the registry.
- Code: make_clip optional group framing, `window` (incl. `emoji_y`), `scene_threshold`; short caption groups merged.
- Not verified: audio by ear, caption accuracy beyond the ASR transcript, rights/campaign terms for the source.

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

## 2026-10-24 - Pet Simulator 99 campaign (BloxClips) - run-2026-10-24-ps99-clip1
- Sources: the 17 campaign footage files (Drive folder), all new. Footage is 1212x1080 gameplay with no speech, and the game audio is near-silent.
- 14 candidates were scored. 6 clips were delivered: 5 Gargantuan reveals (1x1x1x1, Anime Agony, Aura Cat, Black Balloon Cat, Capybara) and a Huge/Titanic 4-hatch compilation. The rest were rejected (common pets, no payoff).
- New renderer `clipper/make_gameplay_clip.py`: format B, teaser hook, written texts, campaign reaction voice with captions, hype bed and a payoff label.
- v1 was rejected (silent audio) and so was v2 (no pet name at the payoff). v3 was delivered.
- QC: technical pass / pass_with_notes. The black and frozen flags are the game's own animation (see output/ps99/editorial_review.md).
- Scheduled on Metricool: Oct 24 17:30 NY, then Oct 25-29 at 11:00 NY.
