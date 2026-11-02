# Deep dive: what goes viral for MW4 / CoD on TikTok right now (2026-11-02)

Method (real data this time, with the domains unlocked):
- Rendered 11 TikTok discover/tag pages in headless Chromium (`clipper/research/tt_browse.js`) and captured the
  JSON the page loads: 363 videos with real play/like/comment/share counts, duration, music and caption
  (`tiktok-scrape-2026-11-02/videos.json`, analysed with `tt_analyze.py`). 190 of them are MW4 posts from the last
  30 days. /tag/ pages returned only 1 item each (login wall); /discover/ pages worked.
- Downloaded and watched 8 of the top videos frame by frame (`tt_video.js`; contact sheets in the folder above).
- Read our campaign page live (contentrewards.com) and two research articles (OpusClip 13.5M-clip study, Eklipse hooks).

## Our campaign, live numbers (MW4 Multiplayer Launch, Clipping Culture)
- TikTok: $1.75 / 1K views, **min payout $5.25 (so a clip needs about 3,000+ views to pay anything)**, max $1,200.
- Instagram: $1.25 / 1K, min $3.75, max $1,200. Budget $12,669 of $23,058 left, 205 clippers. Leaderboard hidden
  unless logged in.

## The winners in our exact niche
| views | account (followers) | what it is |
|---|---|---|
| 19.6M | @siidv2 (694K) | "MW4 looks INSANE 😍". 45 s of continuous MW4 multiplayer, full-screen 9:16, facecam in the corner, small native text "MW4 looks like real life 😍" for the first ~4 s only, original sound, no cuts, no music. Opens on a photoreal rainy street. |
| 5.8M / 4.8M | @major.saif (566K) | "Shopping in MW4 :3" / "Looks so Good👀 \| @Call of Duty". 12-18 s cinematic edits, 18 cuts in 12 s (one every ~0.7 s), tiny native text "MW4 Multiplayer.", square 1:1 frame. |
| 3.2M | @bah7uz (634K) | MW4 edit on "ANTROBEARS (Super Slowed)" phonk, 12.9 s, 10 cuts. |
| 1.5M | @stravos_fn (**206 followers**) | "SON how does THIS get play of the game😂✌️". Raw 16:9 screen recording in the middle of a black frame, small native white text on top, sarcastic about the game's own BEST PLAY replay. |
| 1.1M | @infcted1 (**563 followers**) | "Do not buy MW4" text over 27 s of good, continuous multiplayer (ironic hook). Caption "if you're only playing multiplayer...". |
| 565K | @puffer249 (2.1K) | "'best play' hes ... dead bro 😂", 8 s, the game's BEST PLAY screen. |

Takeaway: brand-new accounts do hit 1M+ in this niche. What they share is a native, unedited look plus one
relatable or funny line, not heavy production.

## Patterns from the 363-video sample
- Content type, median plays: **funny / relatable ~230K** vs "edit" ~23K vs "insane/graphics" ~18K. Funny moments
  also have the highest engagement (often 15-30%).
- Length (MW4, last 30 days): <=15 s median 2.5K, 16-30 s 10K, 31-60 s 5K, 60 s+ 253K (long campaign
  gameplay). The multiplayer hits sit at 27-45 s continuous or 10-18 s fast-cut edits. Our 11-15 s clips are in
  the weakest bucket.
- Sound: almost everything is "original sound" (game audio). Edits that use music use slowed phonk added inside
  TikTok (ANTROBEARS Super Slowed, BREGA DO SANS, RAGE (SLOWED), Pasa La Manguera).
- Text: TikTok-native style (small, white, or the white "bubble"), 3-6 words, on screen for the first 3-5 s only.
  Nobody in the top list uses big branded titles like ours.
- Hashtags in 500K+ videos: #callofduty, #mw4, #cod, #fyp, #edit, #modernwarfare4, #gaming, #modernwarfare.
  About 5 per post in this niche. OpusClip's cross-niche data favours 8-12 with a mix of niche + generic tags
  (#fyp 2.2x median); our niche sample shows no difference, so use about 6-8 mixed.
- Facecam / creator presence helps (@siidv2), but we have no facecam, so a sarcastic text "voice" stands in for it.

## What we do differently today (and change)
1. **Layout**: we put the game in a 3:4 window with a big yellow Anton title on blurred bars, which reads as an
   edited ad. Winners are either full-screen 9:16 or raw 16:9 with a small native text. Next batch: full-screen 9:16
   crop (or raw 16:9 letterbox for meme clips).
2. **Text**: one short native-style line, 3-6 words, first 3-5 s only. The owner can also type it in TikTok's own
   text tool, which looks most native.
3. **Length**: 25-45 s of continuous good gameplay for "looks insane" clips; keep 10-15 s only for fast-cut edits.
4. **Angle**: the funny / relatable "BEST PLAY" meme. Our source literally is the game's Top Plays, so captions like
   "'best play' ..." fit, as long as they stay non-toxic and don't rage-bait (campaign rule).
5. **Hook line ideas within campaign rules**: "MW4 looks like real life 😍", "MW4 Multiplayer." (minimal), "this
   game is crazy", "the details in MW4 👀", "how is this a game". Avoid "Do not buy MW4": that's misleading /
   rage-bait under the brief.
6. **Hashtags**: #mw4 #callofduty #cod #modernwarfare4 #fyp #gaming #codclips, with #Sponsored on its own line.
7. **Sound**: keep the original game audio. If adding music, add a trending slowed phonk in TikTok at low volume.

## Sources
- Live TikTok discover pages: call-of-duty-modern-warfare-4-edits, call-of-duty-edit, cod-clips, mw4-multiplayer,
  funny-cod-moments, cod-montage, mw4-gameplay (scraped 2026-11-02)
- Videos: tiktok.com/@siidv2/video/7699524987396443406, /@major.saif/video/7676016702999596310,
  /@major.saif/video/7697476680373308694, /@bah7uz/video/7701489183881202966, /@stravos_fn/video/7700766645811203358,
  /@infcted1/video/7699759831195847950, /@puffer249/video/7702947622822120718
- https://contentrewards.com/c/campaigns/7a73a53b-2bba-4a5c-8187-05534dd6716d
- https://www.opus.pro/blog/anatomy-of-a-viral-tiktok-2026
- https://blog.eklipse.gg/beginner-guide-2/stream-hook-strategy-first-two-seconds.html
