"""Render vertical Shorts from speechless gameplay footage (campaign clips, e.g. Pet Simulator 99).

usage: python3 -I clipper/make_gameplay_clip.py SPEC.json [--only NAME] [--outdir DIR]

Layout ("format B"): the game window sits in the middle of the 9:16 frame over a dark blurred copy of itself,
a hook title above it, timed on-screen text below it, and a CTA end card. No ASR captions - the footage has no speech,
so every line of text is written in the spec and must describe what is actually on screen.

SPEC.json:
{
  "watermark": "@yourchannel",
  "clips": [{
    "name": "gargantuan-agony",
    "source": "../ps99/clip02.mp4",       # relative to the spec file
    "crop": [354, 0, 1212, 1080],         # game area inside the source frame (x, y, w, h)
    "segments": [[60.0, 61.5], [40.0, 58.0, 1.6], [58.0, 66.0]],  # [start, end, speed]; first can be a teaser
    "title": "GARGANTUAN HATCH IN PET SIM 99",
    "texts": [[40.2, 2.0, "OPENING THE *ANIME* EGG..."], [59.0, 2.5, "GARGANTUAN *AGONY*!"]],  # source time, seconds, text; *word* = highlight
    "payoff": 59.0,                       # source time of the reveal: riser before, flash + punch-in + boom on it
    "emojis": [[59.3, "😱"]],
    "mood": "none",                       # extra music bed under the game audio: none | hype | fun | tense
    "cta": "PLAY PET SIM 99 ON ROBLOX",
    "voice": {"file": "campaign_audio/C.mp3", "words": "campaign_audio/C.json",   # optional voice-over (e.g. the
              "segments": [[0, 9.0]], "align": [7.2, 72.5]}, # campaign's reaction lines): kept segments of the file;
                                          # voice time 7.2 lands on source time 72.5; captions come from the words
                                          # file and replace the written texts while the voice runs
    "labels": [[72.5, "GARGANTUAN ANIME AGONY"]],  # replaces the hook title from that time on (the payoff's name)
    "game_y": 479                         # optional: top of the game window (default centred)
  }]
}
Compilations: a segment may name its own source as a 4th element ([s, e, speed, "../ps99/clip09.mp4"]); set
"times": "output" so texts / payoff / emojis are given in output seconds, and "payoff" may then be a list.
"""
import argparse, json, os, re, subprocess, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_clip import (W, H, FPS, SFX, FONTS, BEDS, ts, ass_escape, emoji_frames, pulse, phrases, build_timeline,
                       clean,
                       windows)

YELLOW = "00E6FF"


def seg_parts(seg):
    s, e = seg[0], seg[1]
    return s, e, (seg[2] if len(seg) > 2 else 1.0)


def to_out(t, segments):
    """first output time showing source time t (segments in order)"""
    acc = 0.0
    for seg in segments:
        s, e, sp = seg_parts(seg)
        if s <= t <= e:
            return acc + (t - s) / sp
        acc += (e - s) / sp
    return None


def total_len(segments):
    return sum((e - s) / sp for s, e, sp in map(seg_parts, segments))


def marked_lines(text, n=18, base_col="FFFFFF"):
    """wrap text into lines of ~n chars; words inside *...* (may span several words) are highlighted"""
    words, hl = [], False
    for w in text.split():
        on = hl or w.startswith("*")
        hl = on and "*" not in w[1:]
        words.append((w.replace("*", ""), on))
    lines, cur = [], []
    for w, on in words:
        if cur and len(" ".join(x for x, _ in cur)) + len(w) + 1 > n:
            lines.append(cur); cur = []
        cur.append((w, on))
    if cur:
        lines.append(cur)
    return [" ".join(f"{{\\c&H{YELLOW}&}}{ass_escape(w)}{{\\c&H{base_col}&}}" if on else ass_escape(w) for w, on in ln)
            for ln in lines]


VOICE_EMPH = {"NO", "WAY", "INSANE", "CRAZY", "REAL"}


def write_ass(path, clip, tmap, total, game_y, game_h, watermark, voice=None):
    title_y = game_y // 2
    text_y = game_y + game_h + (H - game_y - game_h) // 2 - 40
    cta_y = text_y
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Anton,112,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,1,0,1,8,6,5,40,40,0,1
Style: Txt,Montserrat,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H78000000,-1,0,0,0,100,100,1,0,1,7,5,5,50,50,0,1
Style: Cta,Anton,74,&H00FFFFFF,&H00FFFFFF,&H003B3BFF,&H00000000,0,0,0,0,100,100,2,0,3,16,0,5,30,30,0,1
Style: Cap,Montserrat,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,1,0,1,7,5,5,40,40,0,1
Style: Mark,Montserrat,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,1,0,0,100,100,6,0,1,0,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    cta = clip.get("cta", "PLAY PET SIM 99 ON ROBLOX")
    cta_t = max(0, total - 2.6) if cta else total
    # hook title: words land one after another, then the block stays
    # payoff labels (e.g. the pet's name) take over the title area from their time on
    labels = sorted((tmap(t), txt) for t, txt in clip.get("labels", []) if tmap(t) is not None)
    title_end = labels[0][0] if labels else total
    lines = marked_lines(clip["title"].upper(), 18)
    y0 = title_y - (len(lines) - 1) * 62
    for i, ln in enumerate(lines):
        y = y0 + i * 124
        d = i * 90
        ev.append(f"Dialogue: 2,{ts(0)},{ts(title_end)},Title,,0,0,0,,{{\\an5\\move({W // 2},{y - 140},{W // 2},{y},{d},{d + 200})"
                  f"\\frz-3\\t({d + 200},{d + 300},\\frz0)}}{ln}")
    for k, (t, txt) in enumerate(labels):
        end = labels[k + 1][0] if k + 1 < len(labels) else total
        lines = marked_lines(txt.upper(), 16)
        y0 = title_y - (len(lines) - 1) * 62
        for i, ln in enumerate(lines):
            y = y0 + i * 124
            ev.append(f"Dialogue: 2,{ts(t)},{ts(end)},Title,,0,0,0,,{{\\an5\\pos({W // 2},{y})\\fscx30\\fscy30"
                      f"\\t(0,140,\\fscx118\\fscy118)\\t(140,240,\\fscx100\\fscy100)}}{ln}")
    # timed on-screen text (source times -> output times; clipped to the CTA)
    items = []
    for t_src, dur, txt in clip.get("texts", []):
        t = tmap(t_src)
        if t is not None:
            items.append((t, dur, txt))
    if voice:   # the voice captions own the text area while the voice runs
        items = [it for it in items if not voice["at"] - 0.3 <= it[0] <= voice["end"]]
        groups = phrases(voice["words"], VOICE_EMPH)
        for gi, gr in enumerate(groups):
            end = min(groups[gi + 1][0]["s"] if gi + 1 < len(groups) else total, gr[-1]["e"] + 0.4, cta_t)
            for k, w in enumerate(gr):
                t0 = gr[0]["s"] if k == 0 else w["s"]
                t1 = gr[k + 1]["s"] if k + 1 < len(gr) else end
                if t1 - t0 < 0.02:
                    continue
                parts = []
                for j, x in enumerate(gr):
                    txt = ass_escape(x["w"].upper())
                    col = "3B3BFF" if clean(x["w"]) in VOICE_EMPH else YELLOW
                    if j == k:
                        parts.append(f"{{\\c&H{col}&\\fscx118\\fscy118\\t(0,90,\\fscx108\\fscy108)}}{txt}{{\\c&HFFFFFF&\\fscx100\\fscy100}}")
                    else:
                        parts.append(txt)
                enter = f"\\move({W // 2},{text_y + 30},{W // 2},{text_y},0,90)" if k == 0 else f"\\pos({W // 2},{text_y})"
                ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},Cap,,0,0,0,,{{\\an5\\q0{enter}}}" + " ".join(parts))
    items.sort()
    for k, (t, dur, txt) in enumerate(items):
        end = min(t + dur, items[k + 1][0] if k + 1 < len(items) else total, cta_t,
                  voice["at"] if voice and t < voice["at"] else total)
        if end - t < 0.3:
            continue
        col = "FFFFFF"
        for j, ln in enumerate(marked_lines(txt.upper(), 18, col)):
            y = text_y + j * 96
            ev.append(f"Dialogue: 1,{ts(t)},{ts(end)},Txt,,0,0,0,,{{\\an5\\move({W // 2},{y + 40},{W // 2},{y},0,110)\\fad(70,90)"
                      f"\\fscx125\\fscy125\\t(0,110,\\fscx100\\fscy100)}}{ln}")
    if cta:
        ev.append(f"Dialogue: 3,{ts(cta_t)},{ts(total)},Cta,,0,0,0,,{{\\an5\\pos({W // 2},{cta_y})\\fscx40\\fscy40"
                  f"\\t(0,120,\\fscx112\\fscy112)\\t(120,200,\\fscx100\\fscy100)}}{ass_escape(cta.upper())}")
    if watermark:
        ev.append(f"Dialogue: 4,{ts(0)},{ts(total)},Mark,,0,0,0,,{{\\an5\\pos({W // 2},{H - 70})\\alpha&H60&}}{ass_escape(watermark)}")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")
    return cta_t if cta else None


def atempo(sp):
    f = []
    while sp > 2.0:
        f.append("atempo=2.0"); sp /= 2.0
    while sp < 0.5:
        f.append("atempo=0.5"); sp /= 0.5
    f.append(f"atempo={sp:.4f}")
    return ",".join(f)


def render(spec_dir, spec, clip, outdir):
    out = os.path.join(outdir, clip["name"] + ".mp4")
    if os.path.exists(out):
        raise SystemExit(f"{out} already exists - finished clips are never overwritten; give the new version a new name")
    segs = clip["segments"]
    srcs = [os.path.join(spec_dir, sg[3] if len(sg) > 3 else clip["source"]) for sg in segs]
    tmap = (lambda t: t) if clip.get("times") == "output" else (lambda t: to_out(t, segs))
    cx, cy, cw, ch = clip["crop"]
    game_h = int(round(W * ch / cw / 2)) * 2
    game_y = clip.get("game_y", (H - game_h) // 2)
    total = total_len(segs)

    voice = None
    if clip.get("voice"):
        v = clip["voice"]
        vsegs = v["segments"]
        vwords = json.load(open(os.path.join(spec_dir, v["words"])))["words"]
        wout, _, vlen = build_timeline(vsegs, vwords)
        vt, src_t = v["align"]
        at = max(0.0, tmap(src_t) - to_out(vt, vsegs))
        vend = min(total, at + vlen)
        words = [{**w, "s": w["s"] + at, "e": w["e"] + at} for w in wout if w["s"] + at < vend - 0.1]
        voice = {"file": os.path.join(spec_dir, v["file"]), "segments": vsegs, "at": at, "end": vend,
                 "words": words, "db": v.get("db", 0)}

    td = tempfile.mkdtemp()
    ass = os.path.join(td, "text.ass")
    cta_t = write_ass(ass, clip, tmap, total, game_y, game_h, spec.get("watermark"), voice)

    n = len(segs)
    inputs, junctions, acc = [], [], 0.0
    for i, seg in enumerate(segs):
        s, e, sp = seg_parts(seg)
        if i:
            junctions.append((acc, srcs[i] == srcs[i - 1] and seg_parts(segs[i - 1])[1] > s + 1))
        inputs += ["-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", srcs[i]]
        acc += (e - s) / sp
    idx = n
    mood = clip.get("mood", "none")
    bed_idx = None
    if mood in BEDS:
        inputs += ["-stream_loop", "-1", "-i", f"{SFX}/{BEDS[mood]}.wav"]
        bed_idx = idx; idx += 1
    voice_idx = None
    if voice:
        inputs += ["-i", voice["file"]]
        voice_idx = idx; idx += 1
    emojis = []
    for k, (t_src, chr_) in enumerate(clip.get("emojis", [])):
        t = tmap(t_src)
        if t is None:
            continue
        folder = os.path.join(td, f"emoji{k}")
        canvas = emoji_frames(chr_, folder, size=240)
        inputs += ["-framerate", str(FPS), "-i", os.path.join(folder, "%03d.png")]
        emojis.append((idx, t, canvas)); idx += 1

    po = clip.get("payoff")
    payoffs = [t for t in (tmap(x) for x in (po if isinstance(po, list) else [po] if po is not None else [])) if t is not None]
    text_times = [tmap(t) for t, _, _ in clip.get("texts", [])]
    text_times = [t for t in text_times if t is not None and t > 0.5 and all(abs(t - p) > 0.3 for p in payoffs)
                  and not (voice and voice["at"] - 0.3 <= t <= voice["end"])]
    sfx_events = [("impact", 0.0, 0.7, None), ("swoosh", 0.05, 0.5, None)]
    for j, back in junctions:
        sfx_events.append(("rewind" if back else "whoosh", max(0, j - 0.3), 0.6, None))
    for t in text_times:
        sfx_events.append(("pop", t, 0.35, None))
    for _, t, _ in emojis:
        sfx_events.append(("pop", t, 0.45, None))
    for payoff in payoffs:
        if payoff > 2.6:
            sfx_events.append(("riser", payoff - 2.5, 0.45, None))
        sfx_events += [("boom", payoff, 0.9, None), ("bassdrop", payoff, 0.5, None)]
    if cta_t is not None:
        sfx_events.append(("swoosh", cta_t, 0.55, None))
    names = sorted({e[0] for e in sfx_events})
    sfx_idx = {}
    for nm in names:
        inputs += ["-i", f"{SFX}/{nm}.wav"]
        sfx_idx[nm] = idx; idx += 1

    g = []
    for i, seg in enumerate(segs):
        _, _, sp = seg_parts(seg)
        g.append(f"[{i}:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS},format=yuv420p[tv{i}];"
                 f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS,{atempo(sp)}[ta{i}]")
    g.append("".join(f"[tv{i}][ta{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]")
    flashes = [j for j, _ in junctions] + payoffs
    punch = pulse(payoffs, 0.16, 2.2)
    zoom = f"1+0.06*exp(-t*3)+0.02*t/{total:.2f}+{punch}+{pulse([j for j, _ in junctions], 0.05, 7)}"
    shake = pulse(payoffs, 14, 7).replace("exp(", "sin(t*90)*exp(")
    grade = "eq=contrast=1.08:saturation=1.25,unsharp=5:5:0.8:5:5:0"
    g.append(f"[cv]crop={cw}:{ch}:{cx}:{cy},{grade},split[cbg][cfg]")
    g.append(f"[cbg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=30:3,eq=brightness=-0.32:saturation=1.1[bg]")
    g.append(f"[cfg]scale={W}:{game_h},scale=w='trunc({W}*({zoom})/2)*2':h=-2:eval=frame,"
             f"crop={W}:{game_h}:'(iw-ow)/2+{shake}':'(ih-oh)/2'[fg]")
    g.append(f"color=c=white:s={W}x{game_h + 12}:r={FPS},format=yuv420p[edge]")
    g.append(f"[bg][edge]overlay=0:{game_y - 6}:shortest=1[bge]")
    g.append(f"[bge][fg]overlay=0:{game_y},eq=brightness='{pulse(flashes, 0.55, 11)}':eval=frame,"
             f"rgbashift=rh=-10:bh=10:edge=smear:enable='{windows(payoffs, 0.14)}',"
             f"vignette=PI/6[base]")
    cur = "base"
    for k, (ii, t, canvas) in enumerate(emojis):
        x = int(W * (0.82 if k % 2 == 0 else 0.18))
        y = game_y + int(game_h * 0.25)
        g.append(f"[{ii}:v]format=rgba,setpts=PTS-STARTPTS+{t:.3f}/TB[em{k}]")
        g.append(f"[{cur}][em{k}]overlay=x={x - canvas // 2}:y={y - canvas // 2}:eof_action=pass[ov{k}]")
        cur = f"ov{k}"
    g.append(f"[{cur}]ass='{ass}':fontsdir='{FONTS}'[capd]")
    g.append(f"color=c=0xFFE000:s={W}x12:r={FPS}[bar];[capd][bar]overlay=x='-w+w*t/{total:.3f}':y={H - 12}:shortest=1,format=yuv420p[vout]")

    # audio: game sound (kept as the main bed), optional extra music bed, sfx
    g.append("[ca]volume=-2dB[game]")
    mix = ["[game]"]
    if voice:
        nv = len(voice["segments"])
        ms = int(voice["at"] * 1000)
        g.append(f"[{voice_idx}:a]aresample=48000,aformat=channel_layouts=stereo,asplit={nv}" + "".join(f"[vr{k}]" for k in range(nv)))
        for k, (a, b) in enumerate(voice["segments"]):
            g.append(f"[vr{k}]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={max(0, b - a - 0.04):.3f}:d=0.04[vs{k}]")
        g.append("".join(f"[vs{k}]" for k in range(nv)) + f"concat=n={nv}:v=0:a=1,adelay={ms}|{ms},"
                 f"apad,atrim=0:{total:.3f},afade=t=out:st={max(0, voice['end'] - 0.3):.3f}:d=0.3,volume={voice['db']}dB,asplit[voice][vkey]")
        mix.append("[voice]")
    if bed_idx is not None:
        g.append(f"[{bed_idx}:a]atrim=0:{total:.3f},aresample=48000,aformat=channel_layouts=stereo,volume=-16dB,"
                 f"afade=t=in:d=0.3,afade=t=out:st={max(0, total - 1):.3f}:d=1[bedraw]")
        if voice:
            g.append("[bedraw][vkey]sidechaincompress=threshold=0.03:ratio=5:attack=20:release=350[bed]")
        else:
            g.append("[bedraw]anull[bed]")
        mix.append("[bed]")
    elif voice:
        g.append("[vkey]anullsink")
    for nm in names:
        uses = [e for e in sfx_events if e[0] == nm]
        g.append(f"[{sfx_idx[nm]}:a]aresample=48000,aformat=channel_layouts=stereo,asplit={len(uses)}"
                 + "".join(f"[{nm}{k}]" for k in range(len(uses))))
    counter = {}
    for nm, t, vol, dur in sfx_events:
        k = counter.get(nm, 0); counter[nm] = k + 1
        ms = int(t * 1000)
        trim = f"atrim=0:{dur:.3f}," if dur else ""
        g.append(f"[{nm}{k}]{trim}adelay={ms}|{ms},volume={vol}[s_{nm}{k}]")
        mix.append(f"[s_{nm}{k}]")
    g.append("".join(mix) + f"amix=inputs={len(mix)}:normalize=0:duration=first,atrim=0:{total:.3f}[aout]")

    os.makedirs(outdir, exist_ok=True)
    gp = os.path.join(td, "graph.txt")
    open(gp, "w").write(";\n".join(g))
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", gp, "-map", "[vout]", "-map", "[aout]",
           "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    r = subprocess.run(["ffmpeg", "-i", out, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    lufs = float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)[-1])
    tmp = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af",
                    f"volume={-10 - lufs:.2f}dB,alimiter=limit=0.95:attack=2:release=60", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    print(f"{out}  ({total:.1f}s, {len(junctions)} junctions, {len(emojis)} emojis)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--only"); ap.add_argument("--outdir", default="clips")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    base = os.path.dirname(os.path.abspath(a.spec))
    for c in spec["clips"]:
        if not a.only or c["name"] == a.only:
            render(base, spec, c, a.outdir)
