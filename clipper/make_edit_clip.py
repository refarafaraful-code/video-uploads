"""Beat-synced "edit" style clips from one source (trailers): full-screen 9:16, colour grade, cuts on the music's
beat with zoom punches / flashes, animated glowing title cards, and the music taken from the source itself
(campaigns often allow only their own audio).

usage: python3 -I clipper/make_edit_clip.py SPEC.json [--only NAME] [--outdir DIR]

SPEC.json:
{
  "clips": [{
    "name": "mw4s1-maps-edit",
    "source": "source.mp4",
    "music": [18.18, 31.6],          # [start, length] of the source audio used as the soundtrack (continuous)
    "beat": 0.3947,                  # seconds per beat of that music (152 bpm)
    "shots": [[20.2, 4], [34.0, 4, 0.6, 0.45]],   # [source start, length in beats, speed (opt), crop_x 0..1 or "fit" (opt)]
    "titles": [[0, 4, "CANYON"]],    # [start beat, length in beats, text]: big glowing animated title
    "caption": [[0.0, 6.0, "the new MW4 Season 1 maps"]],   # small native text, output seconds
    "grade": "vivid"                 # vivid | dark
  }]
}
"""
import argparse, json, os, subprocess, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_clip import pulse, windows

W, H, FPS = 1080, 1920, 30
FONTS = os.path.expanduser("~/.fonts")
GRADES = {"vivid": "eq=contrast=1.14:saturation=1.45:gamma=0.97,curves=preset=increase_contrast,vibrance=intensity=0.25",
          "dark": "eq=contrast=1.12:saturation=1.25:gamma=1.12:brightness=0.06,vibrance=intensity=0.2"}


def ts(t):
    return f"{int(t // 3600)}:{int(t % 3600 // 60):02d}:{t % 60:05.2f}"


def write_ass(path, clip, beat, total):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Glow,Anton,170,&H0000E1FF,&H00FFFFFF,&H0000A5FF,&H00000000,0,0,0,0,100,100,6,0,1,10,0,5,40,40,0,1
Style: Big,Anton,170,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,6,0,1,4,3,5,40,40,0,1
Style: Native,Montserrat,58,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,2.6,1.5,5,90,90,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = []
    for b0, nb, text in clip.get("titles", []):
        a, e = b0 * beat, min(total, (b0 + nb) * beat)
        y = 760
        anim = "\\fscx140\\fscy140\\t(0,120,\\fscx100\\fscy100)\\fad(40,160)"
        ev.append(f"Dialogue: 0,{ts(a)},{ts(e)},Glow,,0,0,0,,{{\\an5\\pos({W // 2},{y})\\blur18\\alpha&H30&{anim}}}{text}")
        ev.append(f"Dialogue: 1,{ts(a)},{ts(e)},Big,,0,0,0,,{{\\an5\\pos({W // 2},{y}){anim}\\frz-2\\t(120,260,\\frz0)}}{text}")
    for a, e, text in clip.get("caption", []):
        ev.append(f"Dialogue: 2,{ts(a)},{ts(min(e, total))},Native,,0,0,0,,{{\\an5\\pos({W // 2},300)}}{text}")
    open(path, "w", encoding="utf-8").write(head + "\n".join(ev) + "\n")


def render(base, clip, outdir):
    out = os.path.join(outdir, clip["name"] + ".mp4")
    if os.path.exists(out):
        raise SystemExit(f"{out} already exists - finished clips are never overwritten; give the new version a new name")
    src = os.path.join(base, clip["source"])
    beat = clip["beat"]
    shots = [(s[0], s[1], s[2] if len(s) > 2 else 1.0, s[3] if len(s) > 3 else 0.5) for s in clip["shots"]]
    total = sum(nb for _, nb, _, _ in shots) * beat
    m0, mlen = clip["music"]
    assert mlen >= total - 0.05, f"music ({mlen}s) shorter than the cut ({total:.2f}s)"
    td = tempfile.mkdtemp()
    ass = os.path.join(td, "t.ass")
    write_ass(ass, clip, beat, total)
    inputs, g, cuts, acc = [], [], [], 0.0
    for i, (s, nb, sp, cx) in enumerate(shots):
        out_len = nb * beat
        inputs += ["-ss", f"{s:.3f}", "-t", f"{out_len * sp + 0.1:.3f}", "-an", "-i", src]
        base_f = f"[{i}:v]setpts=(PTS-STARTPTS)/{sp},fps={FPS},trim=duration={out_len:.4f},setpts=PTS-STARTPTS"
        if cx == "fit":   # whole 16:9 frame (e.g. an end card with text) over a blurred fill
            g.append(f"{base_f},split[f{i}a][f{i}b];[f{i}a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                     f"boxblur=30:3,eq=brightness=-0.25[f{i}bg];[f{i}b]scale={W}:-2:flags=lanczos[f{i}fg];"
                     f"[f{i}bg][f{i}fg]overlay=0:(H-h)/2,format=yuv420p[v{i}]")
        else:
            g.append(f"{base_f},crop=w='trunc(ih*9/16/2)*2':h=ih:x='(iw-ow)*{cx}':y=0,scale={W}:{H}:flags=lanczos,format=yuv420p[v{i}]")
        if i:
            cuts.append(acc)
        acc += out_len
    n = len(shots)
    inputs += ["-ss", f"{m0:.3f}", "-t", f"{total:.3f}", "-vn", "-i", src]
    g.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[cv]")
    titles = [b0 * beat for b0, _, _ in clip.get("titles", [])]
    zoom = f"1+0.05*exp(-t*4)+{pulse(cuts, 0.07, 9)}+{pulse(titles, 0.06, 6)}"
    shake = pulse(titles, 10, 9).replace("exp(", "sin(t*90)*exp(")
    g.append(f"[cv]{GRADES[clip.get('grade', 'vivid')]},scale=w='trunc({W}*({zoom})/2)*2':h=-2:eval=frame,"
             f"crop={W}:{H}:'(iw-ow)/2+{shake}':'(ih-oh)/2',eq=brightness='{pulse(cuts, 0.35, 14)}':eval=frame,"
             f"rgbashift=rh=-8:bh=8:edge=smear:enable='{windows(cuts, 0.08)}',unsharp=5:5:0.7:5:5:0,vignette=PI/6,"
             f"ass='{ass}':fontsdir='{FONTS}',format=yuv420p[vout]")
    g.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,afade=t=in:d=0.05,"
             f"afade=t=out:st={max(0, total - 0.6):.3f}:d=0.6,loudnorm=I=-10:TP=-1.0:LRA=9[aout]")
    gp = os.path.join(td, "g.txt")
    open(gp, "w").write(";\n".join(g))
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", gp, "-map", "[vout]", "-map", "[aout]",
                    "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
    print(f"{out}  ({total:.1f}s, {n} shots, {len(cuts)} cuts)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--only"); ap.add_argument("--outdir", default="clips")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    base = os.path.dirname(os.path.abspath(a.spec))
    for c in spec["clips"]:
        if not a.only or c["name"] == a.only:
            render(base, c, a.outdir)
