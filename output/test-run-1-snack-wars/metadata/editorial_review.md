# Editorial / visual review — test run 1 (src-snack-wars)

Method: frames every 0.5 s of each export (sheets in `review_frames/`), close-ups where needed, captions read against
`projects/snack-wars/transcript.txt` / `words.json`. **The audio was not listened to** (no audio playback in this
environment); caption accuracy is checked against the automatic transcript only. Technical QC is separate
(`qc_technical.json`).

## Round 1 (rejected drafts — kept in `clips/`, not delivered)
| Draft | Technical QC | Rejected because |
|---|---|---|
| 01_seal_impression_guess | pass | first frame showed stray caption "GAME."; cuts undetected (scene score 0.15–0.24) → slow pans after cuts |
| 01_seal_impression_guess_v2 | pass | last word on the edge; 😳 briefly over Jessica's face |
| 02_salt_licorice_warning | pass | ending cut "pass" ("THAT IS A HARD"); 🤢/💀 over Jessica's face |
| 03_cup_flip_strategy | pass | ending cut ("BUT THAT'S"); 🧠 over Jessica's face; "I GOT A" visible 0.2 s |
| 04_chopstick_hoops | pass | ending cut ("THAT IS THE WAY IT"); 😵 over Jessica's face |
| 04_chopstick_hoops_v2 | **fail** (truncated) | container restart during render |

Fixes: start/end points extended to full words; `scene_threshold` 0.12; emojis moved to the bottom of the video
(`window.emoji_y`); caption groups shown < 0.4 s merged into the next group.

## Round 2 (final versions)
### 01_seal_impression_guess_v3 — PASS (with notes)
- Hook: opens on Jessica holding the "A SEAL" card making the noise (0 s); the guess lands at 3–4 s.
- Speaker check: John is on screen and smirking when "That is me having sex" is said (source 117 s); Jessica reveals the card after.
- Two-shots keep both faces; ending completes "…REMEMBER THIS MOMENT." Emojis no longer cover faces.
- Notes: mild sexual innuendo. Caption "THAT'S GOING TO BE LAYERS OF HUMOR FOR MY LIFE" comes from the ASR and is unverified by ear.

### 02_salt_licorice_warning_v2 — PASS (with notes)
- Teaser ("Epsom salt bath in your mouth") → Jessica tastes it ("No, hard no") → warnings → John tries it → reactions → "hard pass." Story order is the source order apart from the 1.9 s teaser.
- Profanity bleeped ("HOLY S***").
- Notes: inferred caption corrections from ASR: "Joe" → "JOHN", "salt lake" → "SALT LICK" (context-based, not verified by ear). Some lines are heard over the other person's reaction shot (source editing).

### 03_cup_flip_strategy_v2 — PASS (with notes)
- Rules (6 s) → "Hey, I got a strategy" → frantic flipping → "I have one" → "I miscalculated my efficiencies, but that's okay."
- Notes: the source's left score graphic ("1") is outside the vertical crop; the right one ("25") and the dialogue carry the result. "WIN!" caption is ASR-uncertain. Source "WINNER" graphic is cut by the crop.

### 04_chopstick_hoops_v3 — PASS (with notes)
- Rules (5 s) → chaos → "What the fudge and mustard?" → "That's time" → five hoops → claw-machine line; ending complete.
- Notes: 😵 overlaps the score counter (0–0 at that moment) and bowl for ~1.3 s, not a face. "WINNER" graphic cut by the crop; source's own small subtitle appears once alongside ours.

## Not verified
- Audio by ear: dialogue intelligibility, music/SFX balance, sync — only loudness (-10 to -11 LUFS) and silence detection were measured.
- Caption spelling vs the actual speech (ASR-based).
- How the clips perform; whether the source's owner permits reuse (no campaign/license information provided).
