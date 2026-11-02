# Research - CoD MW4 Multiplayer Launch (Clipping Culture), 2026-11-01

Method: web search only. TikTok, Instagram and the campaign site (contentrewards.com) cannot be opened directly from
this cloud session (network policy). Most sources are vendor blogs, so their numbers are directional only. No view
counts are claimed here.

## What other MW4 clippers post (from TikTok search results)
- Short feature-focused clips, one mechanic per clip: movement first look, a returning attachment, a sniper streak,
  proximity chat. Each clip has one clear subject.
- Sponsored campaign posts use the same caption structure the brief asks for: a line of fan text, then @callofduty,
  then #Ad #Advertisement #Sponsored (e.g. a Dan Allen Gaming "Gameplay and Movement First Look" TikTok).
- The beta campaign brief says "edit the source footage into polished clips, do not post it as a raw reel".

## Short-form patterns relevant to gameplay
- Decide in the first 1-2 s: start right before the peak (the kill, the explosion, the slide), with no setup.
- The hook text should be short (3-5 words, one idea), large and readable. For pure action, text must not cover the
  action. Many people watch muted, so the first second has to work silently.
- Burned-in, animated captions are the norm in viral-tier clips (OpusClip 2026 dataset: ~80% burned in, ~79%
  animated). Viral-tier median length is about 41 s, but gameplay hype clips tend to work shorter.
- Clips that travel in CoD: multi-kills, clutches, standout shots, and big visual moments.

## Applied to this campaign
- Hook text from the brief's own tone ("MW4 MP has no business looking this good"), written by us. No invented facts.
- Timed on-screen captions that describe what is on screen (map/scene/action), with no voice (AI voice is banned).
- Original audio kept clearly audible; any music bed stays low.
- 15-30 s clips, each built around one moment (graphics showcase, movement, gunfight, killstreak). Open on the peak.
- Caption: fan line + @callofduty, then #ad on its own line, plus up to 3 hashtags.
- Avoid gore emphasis and "violent/controversial" framing; label the footage as what it is (gameplay vs trailer).

## Sources
- https://www.opus.pro/blog/anatomy-of-a-viral-tiktok-2026
- https://blog.eklipse.gg/beginner-guide-2/stream-hook-strategy-first-two-seconds.html
- https://blog.eklipse.gg/basic-knowledge/best-games-to-stream-for-viral-clips.html
- https://community.skeepers.io/blog/writing-text-hooks/
- https://www.gofaceless.ai/en/blog/mastering-first-impressions-two-second-rule
- https://www.tiktok.com/@danallengaming/video/7648630782138912018
- https://www.tiktok.com/@user11757231720271/video/7645583819294133534
- https://contentrewards.com/discover/24ad920b-d24f-479e-9cef-f22182e4a0c0 (search snippet only, page not reachable)

## Round 2 (2026-11-01): what to make that could go viral
Method: web search again. TikTok, hooked.so and the campaign site cannot be fetched from this session, so the like
counts below come from search snippets and are page-level, not per video.

Findings
- Music-synced edits are the most prominent COD format on TikTok discovery pages. A 120fps Warzone edit cut to a
  song + SFX showed ~358K likes. An MW4 edit built around one dialogue line ("He's always on the watch", a campaign
  line that is not in our footage) showed ~510K likes on its page. https://www.tiktok.com/discover/call-of-duty-edit
  https://www.tiktok.com/discover/call-of-duty-modern-warfare-4-edits
- Clipping Culture's own MW4 campaigns: Beta 59.2M views, Reveal 88.2M, and a Kill Block campaign that asked for an
  "old-school montage-style edit" (39M). Launch pays $1.25 / 1K TikTok views. The Beta brief says "edit the source
  footage into polished clips, do not post it as a raw reel".
  https://contentrewards.com/discover/d98dada6-aa25-48d2-b86f-1c29f2bbdf2c
- "Watch till the end" funny moments, single-shot sniper clips and "POV:" prefixes recur. Comment-prompt formats
  drive the comments that the 0.5% engagement rule needs (pricing guides list 5-10% engagement for gameplay
  content; vendor data, directional only).
- Montage technique: choose the music first, land every kill exactly on a beat, cut on the bar, and use speed ramps
  and flashes on hits. https://blog.eklipse.gg/beginner-guide-2/how-to-make-gaming-montage.html
- Short clips loop automatically on TikTok, and replays add watch time over 100%. Weighting claims (2-3x) are
  unverified. https://faceless.so/blog/looping-short-videos-tutorial-story-seamless-loops

What we were not doing, and now do
1. Beat sync: the earlier clips used the music only as a bed. mw4-beat-montage cuts every 4 beats of the 140 bpm bed
   and puts each kill on the beat (renderer: `beat_hits`, `bed_db`).
2. Comment prompts built into the format: mw4-rate-this-play-v2 asks for a 1-10 rating.
3. Slow motion / speed ramps on the most cinematic moments (car flip, scope kill, Bomb Glider), all from the
   footage, no filters: mw4-slow-motion.
4. All three are about 11-15 s, so TikTok loops them more often.
