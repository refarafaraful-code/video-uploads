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

## 2026-11-01 - CoD MW4 Multiplayer Launch (Clipping Culture) - run-2026-11-01-cod-mw4
- Source: official "Top Plays Finalists" compilation (8:13, 26 plays) from the owner's Drive. The campaign MediaSilo link is blocked by the session network.
- Pre-campaign research is in projects/cod-mw4/research.md (new standing step).
- 5 clips: rain forest car flip, industrial double kill, Bomb Glider streets, snow sniper, street details.
  Rejected: plays with another creator's facecam, the vertical capture, and silent plays.
- Format: centre 3:4 crop, hook title, timed on-screen captions, payoff labels, original audio with a low bed, and no voice (AI voice is banned).
- TikTok/IG captions with @callofduty and #ad on its own line: output/cod-mw4/captions.json. The owner uploads manually.
- Creative batch (same day, owner request): 4 more clips. "Shotgun mains" meme with the player's own quotes and the game's DOUBLE/TRIPLE KILL banners; "Was that a triple?" contrast; "Pick one" (comment 1/2/3); "Map vibe check" montage. Renderer gained a `montage` option. pick-one and map-vibe were re-rendered as v2 after visual review.
- Viral batch (research round 2): beat-synced kill montage, rate-this-play 1-10, slow-motion graphics. The renderer gained `beat_hits` and `bed_db`. An owner pause truncated the publish copies; they were re-encoded and re-QC'd.
- Native batch (after the TikTok deep dive): 5 clips, full-screen or letterbox, one small TikTok-style text line, original audio, 21-41 s. New renderer clipper/make_native_clip.py. Captions use #Sponsored.
- Transformed batch (2026-11-04, after diagnosing low views: campaign posts median 411): rate-every-kill, split-screen sniper vs shotgun, count-the-kills. make_native_clip gained a split layout and per-text position/size.
- 2026-11-05: the MW4 Multiplayer Launch campaign is **Paused** with its budget exhausted ($0 of $23,058 left; 311 clippers, 16.4M approved views). Clipping Culture has opened 'MW4 Season 01 Trailer Clipping' ($1.85/1K, about $12K left).

## 2026-11-05 - CoD MW4 Season 01 Trailer (Clipping Culture) - run-2026-11-05-cod-mw4-s1
- Source: official Season 1 trailer (MediaSilo folder, downloaded directly). Research in projects/cod-mw4-s1/research.md: campaign posts have a median of 179 views; one square-format post got 143K.
- 4 clips in a square native layout with factual labels (Backstab/Canyon new, Shoot House reimagined, DMZ X01) and comment prompts. The burning-soldier shot was cut (violent content ban). Captions use #Sponsored first plus 3 hashtags.
- Owner's 430K-view reference edit was checked against the brief. It does not comply: own gameplay, an outside song, and a promo for another service. Made 3 compliant edits in its style instead (grade, beat cuts on the trailer's own music, glowing map titles). New renderer clipper/make_edit_clip.py.
- 2026-11-06 loop batch: 4 clips of 8-9 s with action from frame 0 and no end card, aimed at completion and rewatch. The owner's clips average ~450 views; the campaign median is 330.
  Two clips (7.1 s and 7.4 s) failed QC's 8 s minimum and were committed by mistake. They were removed and replaced by longer versions.
- 2026-11-07 voice-over batch: 3 clips using the owner's own recorded English voice, with animated captions and the trailer music ducked underneath. New renderer clipper/make_voice_clip.py. Recordings are kept git-ignored in projects/cod-mw4-s1/voice/.
- 2026-11-08 recap batch: 2 horizontal 16:9 condensed-trailer clips (one without text, one with), modelled on a 5.5K-view clip from a small account the owner found. The voice-over clips had stalled at ~100 views.
