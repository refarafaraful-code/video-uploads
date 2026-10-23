# ClippingMaster — Shorts production repo

**Read `production_data/CLIPPINGMASTER.md` first.** It is the owner's standing production policy and applies to every
run (duplicate prevention, no fixed clip quota, scoring, editing philosophy, QC, metadata, reporting). This file
only says how to execute it in this repo. The owner talks Hebrew; reply in Hebrew.

The owner uploads long videos (mostly Jake Paul vlogs) as **GitHub Release assets** of this repo; Claude turns
them into vertical Shorts and, as authorized by the owner, schedules them on YouTube through the **Metricool**
connector.

## Never start producing on your own
Only start a production run when the owner explicitly asks for one ("העליתי סרטון חדש", "make clips", …).

## Production run
1. `bash clipper/setup.sh` (deps, fonts, Parakeet ASR model, synthesized `clipper/sfx/`).
2. **Eligibility before anything else:**
   - `python3 clipper/registry.py releases` classifies every release asset by its GitHub sha256 digest:
     `processed` → skip (unless the owner explicitly authorizes reprocessing that source), `possible_duplicate` →
     investigate (`registry.py check FILE` after download: hash, duration, resolution; compare frames/audio) and ask
     if still unsure, `new` → eligible.
   - `python3 clipper/registry.py verify` must report the registry consistent with the files.
   - If nothing is eligible, stop and tell the owner.
3. Register the source and a run (`status: in_progress`) in `production_data/production_registry.json` before
   rendering (use `registry.load()/save()`, which writes atomically). New project dir: `projects/<slug>/`.
4. Download: `gh api -H "Accept: application/octet-stream" repos/refarafaraful-code/video-uploads/releases/assets/<ID> > projects/<slug>/source.mp4`
   (git-ignored). Probe it (`registry.py hash`).
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
   Never overwrite an existing clip file; new versions get a new name.
8. QC every export: `python3 clipper/qc.py projects/<slug>/clips/*.mp4` **plus** a frame review (contact sheet:
   opening, captions spelling/timing, payoff present, no awkward crops). Fix and re-render failures; anything
   unfixable is `failed`/`needs_review`, not delivered.
9. Titles/metadata per clip: a recommended title + 2 alternatives, 1–2 line description, a few relevant hashtags,
   tags — accurate, no fabricated claims. Store them in the clip's registry entry.
10. Publish copies: `ffmpeg -i in.mp4 -c:v libx264 -preset slow -crf 21 -maxrate 9M -bufsize 18M -c:a copy -movflags +faststart out.mp4`
    into `shorts-<slug>/`, then QC them too. Commit `shorts-<slug>/`, `projects/<slug>/{spec.json,words.json,transcript.txt}`
    and `production_data/` on the `shorts` branch and push.
11. Schedule (authorized by the owner — see `publishing` in the registry; stop if that authorization is revoked):
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
