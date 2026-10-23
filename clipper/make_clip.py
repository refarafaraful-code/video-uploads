"""Render viral-style vertical Shorts from a long video (v2).

usage: python3 make_clip.py SPEC.json [--only NAME] [--outdir DIR]

SPEC.json:
{
  "source": "video.mp4",
  "words": "words.json",                  # from transcribe.py
  "watermark": "@yourchannel",
  "replace": {"AMERICA": "ERICA"},        # fix transcription mistakes (whole words)
  "scene_threshold": 0.32,                # optional: lower for sources whose cuts are low-contrast (same set/background)
  "clips": [{
    "name": "kidnapped",
    "title": "LOGAN KIDNAPPED JAKE'S WIFE",
    "segments": [[971.0, 972.8], [959.4, 976.4]],  # concatenated in order; first can be a teaser hook
    "emphasis": ["ERICA", "TRUNK"],       # extra words to slam (auto-detected ones are added)
    "payoff": 971.1,                      # source time of the punchline: riser, boom, flash, RGB glitch
    "emojis": [[971.9, "😱"], [1001.3, "🚗"]],   # source time + emoji to pop on screen
    "mood": "tense",                      # music bed: tense | fun | hype | none
    "cta": "FOLLOW FOR PART 2",           # end card text (default FOLLOW FOR MORE, "" to disable)
    "frame": "group",                     # optional: keep all significant faces in frame (two-shots); default follows the largest face
    "window": {"fg_y": 300, "fg_h": 1080, "cap_y": 1460, "emoji_y": 1230}   # optional: video window / caption / emoji position
  }]
}
"""
import argparse, json, math, os, re, subprocess, tempfile
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SFX = os.path.join(HERE, "sfx")
YUNET = os.path.join(HERE, "models", "yunet.onnx")
EMOJI_FONT = "/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf"
FONTS = os.path.expanduser("~/.fonts")
W, H, FPS = 1080, 1920, 30
DEFAULT_WINDOW = {"fg_y": 250, "fg_h": 1500, "cap_y": 1330, "emoji_y": None}  # emoji_y None -> fg_y + 330   # foreground video window; blurred copy fills the rest
FG_Y, FG_H, CAP_Y = DEFAULT_WINDOW["fg_y"], DEFAULT_WINDOW["fg_h"], DEFAULT_WINDOW["cap_y"]
TITLE_Y, CTA_Y = 128, 1832

# ASS colours are &HBBGGRR
PALETTE = ["00E6FF", "3CFF6E", "FFE600", "C83EFF", "00A5FF"]  # yellow green cyan pink orange
RED = "3B3BFF"
AUTO_EMPH = {"NO", "NOPE", "YES", "YEP", "NOW", "DAMN", "GUN", "NEVER", "MILLION", "KNOCKOUT", "KO", "WOW",
             "STOP", "MOVE", "RUN", "WHY", "LIAR", "FIGHT", "DEAD", "BROKE", "RICH", "SERIOUSLY", "INSANE",
             "KIDNAPPED", "DRIVE", "JEALOUS", "BASTARD", "DONE"}
BLEEP = {"FUCK", "FUCKING", "FUCKIN", "FUCKED", "MOTHERFUCKER", "SHIT", "BITCH"}
BEDS = {"tense": "bed", "fun": "bed_fun", "hype": "bed_hype"}


def clean(w):
    return re.sub(r"[^A-Z0-9']", "", w.upper())


def ass_escape(s):
    s = "".join(c for c in s if ord(c) < 0x10000)
    return s.replace("\\", "").replace("{", "(").replace("}", ")")


def ts(t):
    t = max(0, t)
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def display(w):
    """caption text for a word: upper case, profanity masked"""
    u = w.upper()
    c = clean(w)
    if c in BLEEP or c == "FING":
        return u[0] + "*" * (len(c) - 1) + u[len(c):] if c != "FING" else "F***ING"
    return u


def load_words(spec):
    words = json.load(open(spec["words"]))["words"]
    rep = {clean(k): v for k, v in spec.get("replace", {}).items()}
    for w in words:
        c = clean(w["w"])
        if c in rep:
            tail = re.search(r"[^A-Za-z0-9']*$", w["w"]).group(0)
            w["w"] = rep[c] + tail
    return words


def build_timeline(segments, words):
    out, junctions, acc = [], [], 0.0
    for i, (s, e) in enumerate(segments):
        if i:
            junctions.append((acc, segments[i - 1][1] > s + 1))  # (time, jumped backwards)
        for w in words:
            if w["s"] >= s - 0.05 and w["e"] <= e + 0.15:
                out.append({**w, "s": acc + w["s"] - s, "e": min(acc + w["e"] - s, acc + e - s), "seg": i})
        acc += e - s
    return out, junctions, acc


def to_out(t, segments):
    acc = 0.0
    for s, e in segments:
        if s <= t <= e:
            return acc + t - s
        acc += e - s
    return None


# ---------------------------------------------------------------- analysis

def scene_cuts(src, segments, threshold=0.32):
    cuts = []
    for s, e in segments:
        r = subprocess.run(["ffmpeg", "-ss", str(s), "-t", str(e - s), "-i", src, "-an", "-vf",
                            f"scale=320:-2,select='gt(scene,{threshold})',showinfo", "-f", "null", "-"],
                           capture_output=True, text=True)
        cuts += [s + float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)]
    return cuts


def rdp(pts, eps):
    """Ramer-Douglas-Peucker on (t, x) points"""
    if len(pts) < 3:
        return pts
    (t0, x0), (t1, x1) = pts[0], pts[-1]
    best, idx = 0, 0
    for i in range(1, len(pts) - 1):
        t, x = pts[i]
        d = abs(x - (x0 + (x1 - x0) * (t - t0) / max(t1 - t0, 1e-6)))
        if d > best:
            best, idx = d, i
    if best > eps:
        return rdp(pts[:idx + 1], eps)[:-1] + rdp(pts[idx:], eps)
    return [pts[0], pts[-1]]


def track_faces(src, segments, cuts_src, crop_frac, mode="largest"):
    """horizontal subject centre (0..1 of source width) over output time, as keyframes"""
    cap = cv2.VideoCapture(src)
    sw, sh = cap.get(cv2.CAP_PROP_FRAME_WIDTH), cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    dw = 640
    dh = int(sh * dw / sw)
    det = cv2.FaceDetectorYN.create(YUNET, "", (dw, dh), 0.7, 0.3, 50)
    step = max(1, int(round(fps / 5)))  # ~5 samples per second
    half = crop_frac / 2
    keys, acc = [], 0.0
    for s, e in segments:
        cap.set(cv2.CAP_PROP_POS_MSEC, s * 1000)
        seg_cuts = [c for c in cuts_src if s < c < e]
        samples, n = [], 0
        while True:
            ok = cap.grab()
            if not ok:
                break
            t = s + n / fps
            if t > e:
                break
            if n % step == 0:
                _, fr = cap.retrieve()
                _, faces = det.detect(cv2.resize(fr, (dw, dh)))
                cx = None
                if faces is not None and len(faces):
                    f = max(faces, key=lambda f: f[2] * f[3] * f[14])
                    cx = (f[0] + f[2] / 2) / dw
                    if mode == "group":
                        # every face at least a quarter the size of the biggest one; centre on the group if it fits
                        big = [g for g in faces if g[2] * g[3] >= 0.25 * f[2] * f[3]]
                        lo = min(g[0] for g in big) / dw
                        hi = max(g[0] + g[2] for g in big) / dw
                        if hi - lo <= crop_frac * 0.95:
                            cx = (lo + hi) / 2
                samples.append((t, cx))
            n += 1
        # smooth within shots, snap across cuts; dead-zone so the camera doesn't wander
        cur, last_valid, out = None, 0.5, []
        for t, cx in samples:
            if any(abs(t - c) < 0.11 for c in seg_cuts) or cur is None:
                cur = None
            target = cx if cx is not None else last_valid
            if cx is not None:
                last_valid = cx
            if cur is None:
                cur = target
                if out:
                    out.append((acc + t - s - 0.01, out[-1][1]))
            elif abs(target - cur) > 0.035:
                cur += (target - cur) * 0.3
            out.append((acc + t - s, min(max(cur, half), 1 - half)))
        keys += rdp(out, 0.012) if out else [(acc, 0.5)]
        acc += e - s
    cap.release()
    return keys


def piecewise(keys):
    """ffmpeg expression interpolating (t, v) keyframes"""
    if len(keys) == 1:
        return f"{keys[0][1]:.4f}"
    terms = [f"lt(t,{keys[0][0]:.3f})*{keys[0][1]:.4f}"]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if t1 - t0 < 1e-3:
            continue
        terms.append(f"gte(t,{t0:.3f})*lt(t,{t1:.3f})*({v0:.4f}+{(v1 - v0) / (t1 - t0):.5f}*(t-{t0:.3f}))")
    terms.append(f"gte(t,{keys[-1][0]:.3f})*{keys[-1][1]:.4f}")
    return "+".join(terms)


# ---------------------------------------------------------------- graphics

def emoji_frames(ch, folder, dur=1.3, size=300):
    """pop-in / wobble / fade animation of an emoji as a PNG sequence"""
    os.makedirs(folder, exist_ok=True)
    font = ImageFont.truetype(EMOJI_FONT, 109)
    base = Image.new("RGBA", (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(base).text((8, 8), ch, font=font, embedded_color=True)
    base = base.crop(base.getbbox()).resize((size, size), Image.LANCZOS)
    canvas = int(size * 1.6)
    n = int(dur * FPS)
    for i in range(n):
        t = i / FPS
        sc = 1.3 * t / 0.1 if t < 0.1 else (1.3 - 0.3 * (t - 0.1) / 0.1 if t < 0.2 else 1 + 0.04 * math.sin(t * 9))
        ang = 18 * math.sin(t * 14) * math.exp(-t * 4)
        a = 1 if t < dur - 0.25 else max(0, (dur - t) / 0.25)
        im = base.resize((max(1, int(size * sc)),) * 2, Image.LANCZOS).rotate(ang, expand=True, resample=Image.BICUBIC)
        if a < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        fr = Image.new("RGBA", (canvas, canvas), (0, 0, 0, 0))
        fr.paste(im, ((canvas - im.width) // 2, (canvas - im.height) // 2), im)
        fr.save(os.path.join(folder, f"{i:03d}.png"))
    return canvas


def phrases(words, emph):
    groups, cur = [], []
    for i, w in enumerate(words):
        gap_before = w["s"] - words[i - 1]["e"] if i else 9
        gap_after = words[i + 1]["s"] - w["e"] if i + 1 < len(words) else 9
        alone = clean(w["w"]) in emph and gap_before > 0.2 and gap_after > 0.2
        chars = sum(len(x["w"]) + 1 for x in cur)
        if cur and (alone or gap_before > 0.3 or len(cur) >= 3 or chars + len(w["w"]) > 17
                    or cur[-1]["seg"] != w["seg"] or re.search(r"[.?!,]$", cur[-1]["w"])):
            groups.append(cur); cur = []
        cur.append(w)
        if alone:
            groups.append(cur); cur = []
    if cur:
        groups.append(cur)
    # a group shown for under 0.4 s cannot be read: fold it into the next one (same segment, max 4 words)
    merged = []
    for i, g in enumerate(groups):
        if merged and merged[-1] is not None and merged[-1][-1]["seg"] == g[0]["seg"] and len(merged[-1]) + len(g) <= 4 \
                and g[0]["s"] - merged[-1][0]["s"] < 0.4:
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)
    return merged


def wrap_title(t, n=20):
    lines, cur = [], ""
    for w in t.split():
        if cur and len(cur) + len(w) + 1 > n:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    return lines + [cur]


def write_ass(path, words, emph, clip, watermark, total):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Montserrat,104,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,1,0,1,7,5,5,30,30,0,1
Style: Glow,Montserrat,104,&H00FFFFFF,&H00FFFFFF,&H00FFFFFF,&H00000000,-1,0,0,0,100,100,1,0,1,16,0,5,30,30,0,1
Style: Title,Anton,84,&H00111111,&H00FFFFFF,&H00FFFFFF,&H00000000,0,0,0,0,100,100,1,0,3,18,0,5,30,30,0,1
Style: Cta,Anton,70,&H00FFFFFF,&H00FFFFFF,&H003B3BFF,&H00000000,0,0,0,0,100,100,2,0,3,14,0,5,30,30,0,1
Style: Mark,Montserrat,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,1,0,0,100,100,6,0,1,0,0,5,40,40,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    groups = phrases(words, emph)
    for gi, g in enumerate(groups):
        end = min(groups[gi + 1][0]["s"] if gi + 1 < len(groups) else total, g[-1]["e"] + 0.45)
        single = len(g) == 1 and clean(g[0]["w"]) in emph
        col = RED if single else PALETTE[gi % len(PALETTE)]
        size = 175 if single else 104
        for k, w in enumerate(g):
            t0 = g[0]["s"] if k == 0 else w["s"]
            t1 = g[k + 1]["s"] if k + 1 < len(g) else end
            if t1 - t0 < 0.02:
                continue
            main, glow = [], []
            for j, x in enumerate(g):
                txt = ass_escape(display(x["w"]))
                is_emph = clean(x["w"]) in emph
                c = RED if is_emph else col
                big = int(size * (1.22 if is_emph and not single else 1))
                if j == k:
                    anim = "\\fscx128\\fscy128\\t(0,90,\\fscx112\\fscy112)"
                    main.append(f"{{\\fs{big}\\c&H{c}&{anim}}}{txt}{{\\fscx100\\fscy100}}")
                    glow.append(f"{{\\fs{big}\\alpha&H40&\\c&H{c}&\\3c&H{c}&{anim}}}{txt}{{\\fscx100\\fscy100}}")
                else:
                    main.append(f"{{\\fs{big}\\c&HFFFFFF&}}{txt}")
                    glow.append(f"{{\\fs{big}\\alpha&HFF&}}{txt}")
            enter = f"\\move({W // 2},{CAP_Y + 40},{W // 2},{CAP_Y},0,100)\\fad(60,0)" if k == 0 else f"\\pos({W // 2},{CAP_Y})"
            shake = "\\frz-6\\t(0,60,\\frz5)\\t(60,120,\\frz-3)\\t(120,200,\\frz0)" if single else ""
            ev.append(f"Dialogue: 0,{ts(t0)},{ts(t1)},Glow,,0,0,0,,{{\\an5{enter}\\blur22{shake}}}" + " ".join(glow))
            ev.append(f"Dialogue: 1,{ts(t0)},{ts(t1)},Cap,,0,0,0,,{{\\an5{enter}\\blur0.8{shake}}}" + " ".join(main))
    title = clip.get("title")
    if title:
        lines = wrap_title(ass_escape(title.upper()))
        y0 = TITLE_Y - (len(lines) - 1) * 52
        for i, ln in enumerate(lines):
            y = y0 + i * 104
            d = i * 80
            ev.append(f"Dialogue: 2,{ts(0)},{ts(total)},Title,,0,0,0,,{{\\an5\\move({W // 2},{y - 160},{W // 2},{y},{d},{d + 220})"
                      f"\\frz-3\\t({d + 220},{d + 320},\\frz0)}}{ln}")
    cta = clip.get("cta", "FOLLOW FOR MORE")
    cta_t = max(0, total - 2.4) if cta else total
    if cta:
        ev.append(f"Dialogue: 3,{ts(cta_t)},{ts(total)},Cta,,0,0,0,,{{\\an5\\pos({W // 2},{CTA_Y})\\fscx40\\fscy40"
                  f"\\t(0,120,\\fscx112\\fscy112)\\t(120,200,\\fscx100\\fscy100)}}{ass_escape(cta.upper())}")
    if watermark:
        ev.append(f"Dialogue: 4,{ts(0)},{ts(cta_t)},Mark,,0,0,0,,{{\\an5\\pos({W // 2},{CTA_Y})\\alpha&H60&}}{ass_escape(watermark)}")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")
    return cta_t if cta else None


def pulse(times, amp, decay):
    return "+".join(f"{amp}*gte(t,{p:.3f})*exp(-(t-{p:.3f})*{decay})" for p in times) or "0"


def windows(times, d):
    return "+".join(f"between(t,{p:.3f},{p + d:.3f})" for p in times) or "0"


# ---------------------------------------------------------------- render

def render(spec, clip, outdir):
    global FG_Y, FG_H, CAP_Y
    win = {**DEFAULT_WINDOW, **clip.get("window", {})}
    FG_Y, FG_H, CAP_Y = win["fg_y"], win["fg_h"], win["cap_y"]
    emoji_y = win["emoji_y"] if win["emoji_y"] is not None else FG_Y + 330
    out = os.path.join(outdir, clip["name"] + ".mp4")
    if os.path.exists(out):
        raise SystemExit(f"{out} already exists - finished clips are never overwritten; give the new version a new name")
    src, segs = spec["source"], clip["segments"]
    words = load_words(spec)
    wout, junctions, total = build_timeline(segs, words)

    emph = {clean(x) for x in clip.get("emphasis", [])} | AUTO_EMPH
    slams, last = [], -9
    for w in wout:
        if clean(w["w"]) in emph and w["s"] - last > 1.5:
            slams.append(w["s"]); last = w["s"]
    bleeps = [(w["s"], w["e"]) for w in wout if clean(w["w"]) in BLEEP]

    cuts_src = scene_cuts(src, segs, spec.get("scene_threshold", 0.32))
    cuts = [c for c in (to_out(x, segs) for x in cuts_src) if c and c > 0.3]
    flashes = [j for j, _ in junctions]
    payoff = to_out(clip["payoff"], segs) if clip.get("payoff") is not None else None
    if payoff is not None:
        flashes.append(payoff)
    glitches = sorted(set([payoff] if payoff is not None else []) | set(slams[::2]))

    sw, sh = map(int, subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                                      "stream=width,height", "-of", "csv=p=0", src],
                                     capture_output=True, text=True).stdout.strip().split(",")[:2])
    crop_frac = min(1.0, sh * W / FG_H / sw)
    keys = track_faces(src, segs, cuts_src, crop_frac, clip.get("frame", "largest"))

    td = tempfile.mkdtemp()
    ass = os.path.join(td, "caps.ass")
    cta_t = write_ass(ass, wout, emph, clip, spec.get("watermark"), total)

    # ---- inputs: each segment seeks on its own, then bed, sfx, emoji sequences
    n = len(segs)
    inputs = []
    for s, e in segs:
        inputs += ["-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", src]
    mood = clip.get("mood", "tense")
    bed_idx, idx = None, n
    if mood in BEDS:
        inputs += ["-stream_loop", "-1", "-i", f"{SFX}/{BEDS[mood]}.wav"]
        bed_idx = idx; idx += 1

    emojis = []
    for k, (t_src, ch) in enumerate(clip.get("emojis", [])):
        t = to_out(t_src, segs)
        if t is None:
            continue
        folder = os.path.join(td, f"emoji{k}")
        canvas = emoji_frames(ch, folder)
        inputs += ["-framerate", str(FPS), "-i", os.path.join(folder, "%03d.png")]
        emojis.append((idx, t, canvas, k)); idx += 1

    sfx_events = [("impact", 0.0, 0.8, None), ("swoosh", 0.05, 0.6, None)]
    for j, back in junctions:
        sfx_events.append(("rewind" if back else "whoosh", max(0, j - 0.35), 0.7, None))
    for s in slams:
        sfx_events.append(("pop", s, 0.4, None))
    for _, t, _, _ in emojis:
        sfx_events.append(("pop", t, 0.5, None))
    if payoff is not None:
        if payoff > 2.6:
            sfx_events.append(("riser", payoff - 2.5, 0.4, None))
        sfx_events += [("boom", payoff, 0.9, None), ("glitch", payoff, 0.45, None)]
    for a, b in bleeps:
        sfx_events.append(("beep", a, 0.35, b - a))
    if cta_t is not None:
        sfx_events.append(("swoosh", cta_t, 0.6, None))
    names = sorted({e[0] for e in sfx_events})
    sfx_idx = {}
    for nm in names:
        inputs += ["-i", f"{SFX}/{nm}.wav"]
        sfx_idx[nm] = idx; idx += 1

    # ---- video
    g = []
    for i in range(n):
        g.append(f"[{i}:v]fps={FPS},setpts=PTS-STARTPTS,format=yuv420p[tv{i}];"
                 f"[{i}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[ta{i}]")
    g.append("".join(f"[tv{i}][ta{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]")

    zoom = (f"1+0.12*exp(-t*3.5)+0.03*t/{total:.2f}+" + pulse(slams, 0.08, 9) + "+" + pulse(cuts, 0.035, 7)
            + "+" + pulse(flashes, 0.07, 6))
    shake = pulse(slams + flashes, 16, 9).replace("exp(", "sin(t*95)*exp(")
    grade = ("eq=contrast=1.15:saturation=1.4:gamma=0.96,"
             "curves=r='0/0 0.5/0.54 1/1':b='0/0.02 0.5/0.47 1/0.96',unsharp=5:5:1.0:5:5:0")
    cx = piecewise(keys)
    g.append(f"[cv]{grade},split[cbg][cfg]")
    g.append(f"[cbg]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:4,eq=brightness=-0.22:saturation=1.2[bg]")
    g.append(f"[cfg]crop=w='trunc(iw*{crop_frac:.4f}/2)*2':h=ih:x='clip(({cx})*iw-ow/2,0,iw-ow)':y=0,"
             f"scale={W}:{FG_H},scale=w='trunc({W}*({zoom})/2)*2':h=-2:eval=frame,"
             f"crop={W}:{FG_H}:'(iw-ow)/2+{shake}':'(ih-oh)/2'[fg]")
    g.append(f"[bg][fg]overlay=0:{FG_Y},eq=brightness='{pulse(flashes, 0.6, 12)}':eval=frame,"
             f"rgbashift=rh=-12:bh=12:rv=4:bv=-4:edge=smear:enable='{windows(glitches, 0.16)}',"
             f"noise=alls=7:allf=t,vignette=PI/5[base]")
    cur = "base"
    for k, (ii, t, canvas, kk) in enumerate(emojis):
        x = int(W * (0.78 if k % 2 == 0 else 0.22))
        y = emoji_y
        g.append(f"[{ii}:v]format=rgba,setpts=PTS-STARTPTS+{t:.3f}/TB[em{k}]")
        g.append(f"[{cur}][em{k}]overlay=x={x - canvas // 2}:y={y - canvas // 2}:eof_action=pass[ov{k}]")
        cur = f"ov{k}"
    g.append(f"[{cur}]ass='{ass}':fontsdir='{FONTS}'[capd]")
    g.append(f"color=c=0xFFE000:s={W}x12:r={FPS}[bar];[capd][bar]overlay=x='-w+w*t/{total:.3f}':y={H - 12}:shortest=1,format=yuv420p[vout]")

    # ---- audio: voice (bleeped) + ducked bed + sfx
    mute = "+".join(f"between(t,{a:.3f},{b:.3f})" for a, b in bleeps) or "0"
    g.append(f"[ca]highpass=f=70,acompressor=threshold=-20dB:ratio=3:attack=5:release=120,"
             f"volume=0:enable='{mute}',asplit[voice][key]")
    mix = ["[voice]"]
    if bed_idx is not None:
        g.append(f"[{bed_idx}:a]atrim=0:{total:.3f},aresample=48000,aformat=channel_layouts=stereo,volume=-15dB,"
                 f"afade=t=in:d=0.3,afade=t=out:st={max(0, total - 1):.3f}:d=1[bedraw];"
                 "[bedraw][key]sidechaincompress=threshold=0.03:ratio=6:attack=20:release=400[bed]")
        mix.append("[bed]")
    else:
        g.append("[key]anullsink")
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
    out = os.path.join(outdir, clip["name"] + ".mp4")
    gp = os.path.join(td, "graph.txt")
    open(gp, "w").write(";\n".join(g))
    cmd = ["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", gp, "-map", "[vout]", "-map", "[aout]",
           "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS),
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", out]
    subprocess.run(cmd, check=True)
    # bring to a hot, Shorts-level -9 LUFS
    r = subprocess.run(["ffmpeg", "-i", out, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
    lufs = float(re.findall(r"I:\s+(-?[0-9.]+) LUFS", r.stderr)[-1])
    tmp = out + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", out, "-c:v", "copy", "-af",
                    f"volume={-9 - lufs:.2f}dB,alimiter=limit=0.95:attack=2:release=60", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, out)
    print(f"{out}  ({total:.1f}s, {len(slams)} slams, {len(cuts)} cuts, {len(emojis)} emojis, {len(bleeps)} bleeps, {len(keys)} track keys)")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--only"); ap.add_argument("--outdir", default="clips")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    base = os.path.dirname(os.path.abspath(a.spec))
    for k in ("source", "words"):
        spec[k] = os.path.join(base, spec[k])
    for c in spec["clips"]:
        if not a.only or c["name"] == a.only:
            render(spec, c, a.outdir)
