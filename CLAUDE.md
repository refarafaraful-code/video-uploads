# Shorts clipping pipeline

The owner uploads long YouTube videos (mostly Jake Paul vlogs) here as **GitHub Release assets**; Claude turns them
into viral vertical Shorts and schedules them to the owner's YouTube channel through the **Metricool** connector.
The owner talks Hebrew; reply in Hebrew.

## Workflow for a new video
1. `bash clipper/setup.sh` (installs deps, fonts, Parakeet ASR model, synthesizes `clipper/sfx/`).
2. Find the new asset: `gh api repos/refarafaraful-code/video-uploads/releases --jq '.[] | .tag_name, (.assets[] | [.id,.name])'`
   (releases are often drafts — that's fine). Download:
   `gh api -H "Accept: application/octet-stream" repos/refarafaraful-code/video-uploads/releases/assets/<ID> > projects/<name>/source.mp4`
3. `python3 -I clipper/transcribe.py projects/<name>/source.mp4 projects/<name>/words.json > projects/<name>/transcript.txt`
4. Read the transcript, pick the 4–5 strongest moments (conflict, pranks, reveals, fails, quotable lines), check them
   visually with ffmpeg contact sheets, and write `projects/<name>/spec.json` (format: docstring of
   `clipper/make_clip.py`; `projects/kidnapped-wife/spec.json` is the reference v2 spec). Keep clips 25–60 s,
   open with the strongest line (a teaser segment that jumps back is fine), set `payoff`, `emojis`, `mood`,
   and `replace` for names the ASR gets wrong.
5. `python3 -I clipper/make_clip.py projects/<name>/spec.json --outdir projects/<name>/clips` (~3–4 min per clip),
   inspect frames, send the clips to the owner.
6. Publish: re-encode under GitHub's 50 MB soft limit
   (`ffmpeg -i in.mp4 -c:v libx264 -preset slow -crf 21 -maxrate 9M -bufsize 18M -c:a copy -movflags +faststart out.mp4`),
   commit them to `shorts-<name>/` on the `shorts` branch and push. The repo is public, so Metricool can fetch
   `https://raw.githubusercontent.com/refarafaraful-code/video-uploads/shorts/shorts-<name>/<file>.mp4`.
7. Schedule with Metricool `createScheduledPost` (brand/blogId `7616437`): one Short per day at
   **15:00 America/New_York** (the audience is American), `youtubeData` type `short`, privacy `public`,
   `madeForKids: false`, category `ENTERTAINMENT`, an English title ending in an emoji + `#shorts`, a 1–2 line
   description with hashtags, and tags. Continue after the last already-scheduled day (`getScheduledPosts`).

## Environment notes (cloud session)
- YouTube downloads fail from cloud IPs (bot check / 403) even with the network opened — always use release uploads.
- HuggingFace is blocked; models come from GitHub releases. Creating releases via the API is not permitted for
  this session type, but reading/downloading assets and pushing commits works.
- Source videos and rendered clips are not committed except the publish copies in `shorts-*/`.
