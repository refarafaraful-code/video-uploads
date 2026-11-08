# Research - CoD MW4 Season 01 Trailer campaign (2026-11-05)

Source: official Season 1 Premium trailer (MediaSilo campaign folder, 1080p derivative, 2:18). Facts are from the
official blog (callofduty.com, Oct 28 2026). Season 1 goes live November 6. Launch MP maps: **Backstab (brand-new),
Canyon (brand-new), Shoot House (reimagined)**. Mid-season: Ministry, Overflow and [CLASSIFIED]. DMZ: new location
**X01 (Black Site)**. Kill Block combo "Crash". Shipment was added pre-season.

TikTok check (scraped mw4-season-1 / trailer / new-maps discover pages; 57 recent Season 1 posts, 26 of them
campaign posts):
- Campaign posts: median 179 views, so the same problem as the last campaign.
- One breakout: @ryl_editss (1,956 followers), **143K views**. 10.5 s, square 1:1 trailer footage on black, one
  small white line at the top ("Season 1 of MW4 is already here with new updates 😮"), original trailer audio, no
  music, cuts from Shoot House to Backstab.
- @whatthetier (756 followers), 31.9K: a static "Season 1 roadmap" infographic for 12 s with a "what are you most
  hyped for?" prompt. This is the information format.
- Big creators (tridzoid, tastyhusband) win with "everything you need to know" explainers 60-150 s long, using their
  own gameplay.

Applied:
- Square 1:1 layout (new `square` option in make_native_clip.py), small native text, original trailer audio only
  (music only from the folder is allowed; the trailer track is from the folder).
- Information value instead of raw footage: map names labelled with their real status (brand-new / reimagined),
  the X01 DMZ location, and a comment prompt.
- 11-22 s. Each clip ends on the official "Season 1 - November 6" card from the trailer itself.
- Removed the burning-soldier shot (brief bans violent content). Footage is labelled as trailer content, not
  gameplay.

## Round 2 (2026-11-06): from ~450 views to 1K
- Owner's clips now average 400-450 views. Fresh scrape of the Season 1 campaign posts: median 330 views, and only 1
  post of 8 is over 1K. That one is still @ryl_editss: 10.5 s, square, starts in action, one line, no end card.
  So our clips are already above the campaign median.
- 300-500 views means the clip passed TikTok's first test batch and failed the second, which is decided by
  completion and rewatch (watch time over 100%). https://www.lilachbullock.com/why-tiktok-views-stop-at-300/
  https://multilogin.com/blog/tiktok-views-stuck/ https://metricool.com/how-to-get-more-views-on-tiktok/
- Our earlier S1 clips were 11-22 s and most ended on the trailer's static "Season 1 / Nov 6" card (2-2.5 s of
  no motion, which invites a swipe). Several opened on an aerial shot or a title card instead of action.
Changes in the loop batch: 8-9 s, action in frame 0, no end card, last shot flows back into the first (loop), one
line of text, original trailer audio.

## Round 3 (2026-11-08): the owner's 5.5K-view reference (small account, crossed 1K)
- 34.7 s, **horizontal 16:9 (1024x576), shown letterboxed**, no added text at all. A condensed "whole trailer in
  35 s" recut that keeps the trailer's own title cards (THIS IS MULTIPLAYER / CANYON / SHOOT HOUSE / BACKSTAB /
  THIS IS KILL BLOCK / DMZ X01 / end card) and the **trailer's own audio cut with each shot** (cross-correlation
  0.3-0.6 against the trailer at the matching positions; not an outside song). Cuts every ~0.6 s, with the
  trailer's black flashes kept.
- What we did differently: cropped to 9:16 or square, added text and captions, a single map or theme per clip,
  8-17 s. Our voice-over clips also stalled (~100 views overnight).
- Applied: mw4s1-recap (horizontal, no text, 31 s, full tour MP -> Kill Block -> DMZ -> end card) and
  mw4s1-recap-text-v2 (the same with one small native line). Posting both is an A/B test of text vs no text.
- QC flags the black title cards as "black frames"; they are the trailer's own cards, intended.

## Round 4 (2026-11-08): first real analytics from the owner
- Canyon loop (9 s, best clip, 412 views): average watch 3.8 s, full watch 10%, **For You 97.7%**, viewers
  **95.5% Israel**, 0.7% US.
- Recap (31 s horizontal, 91 views): average watch 2.3 s, full watch 0%.
Reading: TikTok does distribute the clips (almost all views come from For You), but to an Israeli audience,
because the account and device are in Israel. The pool of Israeli viewers for English CoD trailer clips is small,
which explains the ~100-500 ceiling across every format. Within that, shorter loops hold attention best (9 s loop >
voice-over 12 s > 31 s recap). Hebrew is not allowed (brief: English only). Whether Israel counts as Tier 1-2 for
payout is unknown; the owner should ask Clipping Culture.
Applied: 4 more 8 s square loops; stop long formats and voice-overs for this account.
