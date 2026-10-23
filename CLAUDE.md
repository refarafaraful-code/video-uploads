# ClippingMaster — Shorts production repo

The owner's standing production policy is imported below and applies to every run (duplicate prevention, no fixed
clip quota, scoring, editing philosophy, QC, metadata, reporting). This file only says how to execute it in this
repo. Reply in the language the owner writes in (usually Hebrew).

@production_data/CLIPPINGMASTER.md

The owner uploads long videos (mostly Jake Paul vlogs) as **GitHub Release assets** of this repo; Claude turns
them into vertical Shorts. Scheduling on YouTube goes through the **Metricool** connector and needs the owner's
approval per batch (see Publishing).

## Never start producing on your own
Only start a production run when the owner explicitly asks for one ("העליתי סרטון חדש", "make clips", …).

## Production run
1. `bash clipper/setup.sh` (deps, fonts, Parakeet ASR model, synthesized `clipper/sfx/`).
2. **Eligibility before anything else:**
   - `python3 clipper/registry.py verify` must report the registry consistent with the files.
   - `python3 clipper/registry.py releases` pre-screens every release asset by its GitHub sha256 digest.
     `processed` → skip (unless the owner explicitly authorizes reprocessing that source). Anything else is only
     *unknown so far*: a digest miss does not rule out a renamed, trimmed or re-encoded copy.
   - Download each non-processed asset:
     `gh api -H "Accept: application/octet-stream" repos/refarafaraful-code/video-uploads/releases/assets/<ID> > projects/<slug>/source.mp4`
     (git-ignored) and run `python3 clipper/registry.py check projects/<slug>/source.mp4` (sha256, audio
     fingerprint against every registered source, our own clip hashes, metadata). Exit code 0 = `new` → eligible;
     `processed` → skip and report; `possible_duplicate` → compare frames/audio yourself and ask the owner if still
     unsure. Never process a `possible_duplicate` silently.
   - If nothing is eligible, stop and tell the owner.
3. Register: `python3 clipper/registry.py register-source projects/<slug>/source.mp4 --id src-<slug> --title "…" --creator "…" --tag <tag> --asset-id <ID> --project projects/<slug>`
   (refuses duplicates; stores hash, probe and fingerprint; status `in_progress`). Then add a run entry
   (`status: in_progress`) with `registry.load()/save()` (atomic writes) and keep it updated as the run progresses.
4. Probe the source (`registry.py hash`) for resolution/fps/audio before planning crops.
5. Analyze the whole video: `python3 -I clipper/transcribe.py projects/<slug>/source.mp4 projects/<slug>/words.json > projects/<slug>/transcript.txt`,
   read the full transcript, use scene cuts / loudness peaks, and check candidates visually with ffmpeg contact
   sheets. Record every candidate considered with its 0–100 score breakdown (hook 25, curiosity 20, payoff 20,
   clarity 15, pacing 10, distinctiveness 10) and reason for acceptance/rejection in the run's registry entry.
   Select every distinct candidate ≥ 75 that also passes judgment — no quota.
6. Write `projects/<slug>/spec.json` (format: docstring of `clipper/make_clip.py`; `projects/kidnapped-wife/spec.json`
   is the reference). Clips 25–60 s, open on the strongest true moment (a teaser that jumps back is fine), keep
   meaning intact, set `payoff`, `emojis` (only where they fit), `mood`, `replace` for ASR name errors.
   Effects must serve the moment.
7. Render: `python3 -I clipper/make_clip.py projects/<slug>/spec.json --outdir projects/<slug>/clips`.
   It refuses to overwrite an existing file; new versions get a new name.
8. QC every export, two separate layers, and record both in the clip's `qc` entry:
   - technical: `python3 clipper/qc.py projects/<slug>/clips/*.mp4` (format, duration, audio, decode errors,
     black/frozen/silent stretches, loudness, identical-to-registered-clip). Only `pass`/`pass_with_notes` may ship.
   - editorial/visual (not automated): contact sheets + frames at hook, each caption change and the payoff; check
     caption spelling against the audio/transcript, framing of faces/action, hook in the first second, payoff
     included, meaning not distorted.
   Fix and re-render failures; anything unfixable is `failed`/`needs_review`, not delivered.
9. Titles/metadata per clip: a recommended title + 2 alternatives, 1–2 line description, a few relevant hashtags,
   tags — accurate, no fabricated claims. Store them in the clip's registry entry.
10. Publish copies: `ffmpeg -i in.mp4 -c:v libx264 -preset slow -crf 21 -maxrate 9M -bufsize 18M -c:a copy -movflags +faststart out.mp4`
    into `shorts-<slug>/`, then QC them too. Commit `shorts-<slug>/`, `projects/<slug>/{spec.json,words.json,transcript.txt}`
    and `production_data/` on the `shorts` branch and push.
11. **Publishing — only with approval.** Default (`publishing.mode = confirm_each_batch` in the registry): send the
    clips + metadata and ask whether to schedule this batch; do nothing until the owner says yes for it. Only if the
    registry records an explicit standing authorization may you schedule without asking. When approved:
    Metricool `createScheduledPost`, blogId `7616437`, media
    `https://raw.githubusercontent.com/refarafaraful-code/video-uploads/shorts/shorts-<slug>/<file>.mp4`,
    one Short per day at **15:00 America/New_York** continuing after the last day in `getScheduledPosts`,
    `youtubeData` type `short`, privacy `public`, `madeForKids: false`, category `ENTERTAINMENT`. Record the
    Metricool uuid and time; status stays `scheduled` until publication is actually verified.
12. Finish the run in the registry (`completed`/`failed`/…), add an entry to `production_data/production_log.md`,
    run `registry.py verify`, send the clips to the owner, and give the report from CLIPPINGMASTER §16.

## Environment notes (cloud session)
- YouTube downloads fail from cloud IPs (bot check / 403) even with the network opened — always use release uploads.
- HuggingFace is blocked; models come from GitHub releases. Creating releases via the API is not permitted for
  this session type, but reading/downloading assets and pushing commits works.
- `/home/user/clips/...` paths in the registry are historical session paths that no longer exist in new sessions.
- Source videos and master renders are not committed (size); publish copies in `shorts-*/` are.
