"""Render "native-looking" TikTok gameplay clips: no titles, bars or SFX, just the footage and one short
TikTok-style text line (research 2026-11-02: the niche's top posts look unedited).

usage: python3 -I clipper/make_native_clip.py SPEC.json [--only NAME] [--outdir DIR]

SPEC.json:
{
  "clips": [{
    "name": "mw4-native-real-life",
    "source": "source.mp4",                 # relative to the spec file
    "layout": "full",                       # full: 9:16 centre crop filling the screen | letterbox: whole 16:9 frame, black around
                                            # | square: 1:1 centre crop, black around
    "crop_x": 0.5,                          # optional (full): horizontal centre of the crop, 0..1
    "segments": [[241.0, 268.3]],           # source seconds, played in order (hard cuts between them)
    "text": [[0.0, 4.0, "MW4 looks like real life"]]   # output seconds, text; TikTok-like white text, upper third
                                            # optional 4th/5th items: y position (px) and font size
  }]
}
layout "split": two plays at once, stacked: "segments" is the top play, "segments_b" the bottom one (same total
length); both halves are 1080x960 centre crops; audio of both is mixed.

"""
import argparse, json, os, re, subprocess, tempfile

W, H, FPS = 1080, 1920, 30
FONTS = os.path.expanduser("~/.fonts")


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def write_ass(path, items, text_y):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Native,Montserrat,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2.6,1.5,5,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for it in items:
        a, b, t = it[:3]
        y = it[3] if len(it) > 3 else text_y
        fs = f"\\fs{it[4]}" if len(it) > 4 else ""
        ev.append(f"Dialogue: 0,{ts(a)},{ts(b)},Native,,0,0,0,,{{\\an5\\pos({W // 2},{y}){fs}}}{t.replace('{', '(').replace('}', ')')}")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")


def render(base, clip, outdir):
    out = os.path.join(outdir, clip["name"] + ".mp4")
    if os.path.exists(out):
        raise SystemExit(f"{out} already exists - finished clips are never overwritten; give the new version a new name")
    src = os.path.join(base, clip["source"])
    segs = clip["segments"]
    total = sum(e - s for s, e in segs)
    layout = clip.get("layout", "full")
    td = tempfile.mkdtemp()
    ass = os.path.join(td, "t.ass")
    if layout == "split":
        return render_split(src, clip, out, td, ass, total)
    if layout == "square":   # 1:1 centre of the 16:9 frame, black around (as the best Season 1 trailer clips do)
        sq_y = (H - W) // 2
        frame = f"crop=w=ih:h=ih:x=(iw-ow)/2:y=0,scale={W}:{W}:flags=lanczos,pad={W}:{H}:0:{sq_y}:black"
        text_y = sq_y - 90
        write_ass(ass, clip.get("text", []), text_y)
    elif layout == "full":
        frame = f"crop=w='trunc(ih*9/16/2)*2':h=ih:x='(iw-ow)*{clip.get('crop_x', 0.5)}':y=0,scale={W}:{H}:flags=lanczos"
        text_y = 560
    if layout == "letterbox":
        gh = int(W * 9 / 16) // 2 * 2
        frame = f"scale={W}:{gh}:flags=lanczos,pad={W}:{H}:0:(oh-ih)/2:black"
        text_y = (H - gh) // 2 - 70
    if layout != "square":
        write_ass(ass, clip.get("text", []), text_y)
    inputs, g = [], []
    for i, (s, e) in enumerate(segs):
        inputs += ["-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", src]
        g.append(f"[{i}:v]fps={FPS},setpts=PTS-STARTPTS,format=yuv420p[v{i}];[{i}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[a{i}]")
    n = len(segs)
    g.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[cv][ca]")
    g.append(f"[cv]{frame},unsharp=5:5:0.6:5:5:0,ass='{ass}':fontsdir='{FONTS}',format=yuv420p[vout]")
    g.append("[ca]loudnorm=I=-11:TP=-1.0:LRA=11[aout]")
    gp = os.path.join(td, "g.txt")
    open(gp, "w").write(";\n".join(g))
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", gp, "-map", "[vout]", "-map", "[aout]",
                    "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
    print(f"{out}  ({total:.1f}s, {layout}, {n} segment(s))")


def render_split(src, clip, out, td, ass, total):
    segs_b = clip["segments_b"]
    assert abs(sum(e - s for s, e in segs_b) - total) < 0.05, "split halves must have the same length"
    write_ass(ass, clip.get("text", []), H // 2)
    inputs, g = [], []
    k = 0
    for tag, segs in (("t", clip["segments"]), ("b", segs_b)):
        for i, (s, e) in enumerate(segs):
            inputs += ["-ss", f"{s:.3f}", "-t", f"{e - s:.3f}", "-i", src]
            g.append(f"[{k}:v]fps={FPS},setpts=PTS-STARTPTS,format=yuv420p[{tag}v{i}];[{k}:a]aresample=48000,aformat=channel_layouts=stereo,asetpts=PTS-STARTPTS[{tag}a{i}]")
            k += 1
        n = len(segs)
        g.append("".join(f"[{tag}v{i}][{tag}a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[{tag}cv][{tag}ca]")
        g.append(f"[{tag}cv]crop=w='trunc(ih*{W}/{H // 2}/2)*2':h=ih:x='(iw-ow)/2':y=0,scale={W}:{H // 2}:flags=lanczos[{tag}f]")
    g.append(f"[tf][bf]vstack=inputs=2,drawbox=x=0:y={H // 2 - 3}:w={W}:h=6:color=black:t=fill,unsharp=5:5:0.6:5:5:0,"
             f"ass='{ass}':fontsdir='{FONTS}',format=yuv420p[vout]")
    g.append("[tca][bca]amix=inputs=2:normalize=0,loudnorm=I=-11:TP=-1.0:LRA=11[aout]")
    gp = os.path.join(td, "g.txt")
    open(gp, "w").write(";\n".join(g))
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", gp, "-map", "[vout]", "-map", "[aout]",
                    "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
    print(f"{out}  ({total:.1f}s, split)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--only"); ap.add_argument("--outdir", default="clips")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    base = os.path.dirname(os.path.abspath(a.spec))
    for c in spec["clips"]:
        if not a.only or c["name"] == a.only:
            render(base, c, a.outdir)
