"""Voice-over clips: the owner's recorded voice over source footage (e.g. a campaign trailer), with word-by-word
animated captions (make_clip's caption style), a ducked music bed from the source itself, graded 9:16 video and
cuts timed to the words.

usage: python3 -I clipper/make_voice_clip.py SPEC.json [--only NAME] [--outdir DIR]

SPEC.json:
{
  "clips": [{
    "name": "mw4s1-vo-maps",
    "source": "source.mp4",                    # footage (and music bed) source, relative to the spec
    "voice": "voice/rec2.m4a",                 # the recording
    "words": "voice/rec2.json",                # transcribe.py output for the recording
    "fix": {"2": "launch,"},                   # word index -> corrected text ("" drops the word, its time goes to the previous one)
    "emphasis": ["BACKSTAB", "CANYON"],
    "shots": [[13.0, 1.4, "fit"], [2.4, 1.9]], # [source start, seconds, crop_x 0..1 or "fit"]; cover the voice length
    "bed": [20.15, -15]                        # [source start of the music bed, level dB]; ducked under the voice
  }]
}
"""
import argparse, json, os, subprocess, tempfile, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_clip as mc
from make_edit_clip import GRADES

W, H, FPS = 1080, 1920, 30


def load_words(base, clip):
    words = json.load(open(os.path.join(base, clip["words"])))["words"]
    fix = {int(k): v for k, v in clip.get("fix", {}).items()}
    out = []
    for i, w in enumerate(words):
        w = dict(w)
        if i in fix:
            if fix[i] == "":
                if out:
                    out[-1]["e"] = w["e"]
                continue
            w["w"] = fix[i]
        w["seg"] = 0
        out.append(w)
    return out


def render(base, clip, outdir):
    out = os.path.join(outdir, clip["name"] + ".mp4")
    if os.path.exists(out):
        raise SystemExit(f"{out} already exists - finished clips are never overwritten; give the new version a new name")
    src = os.path.join(base, clip["source"])
    voice = os.path.join(base, clip["voice"])
    words = load_words(base, clip)
    shots = [(s[0], s[1], s[2] if len(s) > 2 else 0.5) for s in clip["shots"]]
    total = sum(d for _, d, _ in shots)
    vlen = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", voice],
                                capture_output=True, text=True).stdout)
    assert total >= words[-1]["e"] + 0.2, f"shots ({total:.2f}s) end before the voice ({words[-1]['e']:.2f}s)"
    td = tempfile.mkdtemp()
    ass = os.path.join(td, "caps.ass")
    mc.CAP_Y = 1250
    emph = {mc.clean(x) for x in clip.get("emphasis", [])}
    mc.write_ass(ass, words, emph, {"title": "", "cta": ""}, None, total)

    inputs, g, cuts, acc = [], [], [], 0.0
    for i, (s, d, cx) in enumerate(shots):
        inputs += ["-ss", f"{s:.3f}", "-t", f"{d + 0.1:.3f}", "-an", "-i", src]
        base_f = f"[{i}:v]fps={FPS},trim=duration={d:.4f},setpts=PTS-STARTPTS"
        if cx == "fit":
            g.append(f"{base_f},split[f{i}a][f{i}b];[f{i}a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                     f"boxblur=30:3,eq=brightness=-0.25[f{i}bg];[f{i}b]scale={W}:-2:flags=lanczos[f{i}fg];"
                     f"[f{i}bg][f{i}fg]overlay=0:(H-h)/2,format=yuv420p[v{i}]")
        else:
            g.append(f"{base_f},crop=w='trunc(ih*9/16/2)*2':h=ih:x='(iw-ow)*{cx}':y=0,scale={W}:{H}:flags=lanczos,format=yuv420p[v{i}]")
        if i:
            cuts.append(acc)
        acc += d
    n = len(shots)
    vi, bi = n, n + 1
    bed0, bed_db = clip.get("bed", [None, -15])
    inputs += ["-i", voice]
    if bed0 is not None:
        inputs += ["-ss", f"{bed0:.3f}", "-t", f"{total:.3f}", "-vn", "-i", src]
    g.append("".join(f"[v{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[cv]")
    zoom = f"1+0.04*exp(-t*4)+0.015*t/{total:.2f}+{mc.pulse(cuts, 0.05, 9)}"
    g.append(f"[cv]{GRADES[clip.get('grade', 'vivid')]},scale=w='trunc({W}*({zoom})/2)*2':h=-2:eval=frame,"
             f"crop={W}:{H}:(iw-ow)/2:(ih-oh)/2,eq=brightness='{mc.pulse(cuts, 0.25, 14)}':eval=frame,"
             f"unsharp=5:5:0.6:5:5:0,vignette=PI/6,ass='{ass}':fontsdir='{mc.FONTS}',format=yuv420p[vout]")
    g.append(f"[{vi}:a]aresample=48000,aformat=channel_layouts=stereo,highpass=f=80,"
             f"acompressor=threshold=-22dB:ratio=3:attack=5:release=120,volume=4dB,apad,atrim=0:{total:.3f},asplit[voice][key]")
    if bed0 is not None:
        g.append(f"[{bi}:a]aresample=48000,aformat=channel_layouts=stereo,volume={bed_db}dB,"
                 f"afade=t=in:d=0.2,afade=t=out:st={max(0, total - 0.6):.3f}:d=0.6[bedraw];"
                 "[bedraw][key]sidechaincompress=threshold=0.02:ratio=8:attack=15:release=300[bed]")
        g.append(f"[voice][bed]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-11:TP=-1.0:LRA=9[aout]")
    else:
        g.append("[key]anullsink;[voice]loudnorm=I=-11:TP=-1.0:LRA=9[aout]")
    gp = os.path.join(td, "g.txt")
    open(gp, "w").write(";\n".join(g))
    os.makedirs(outdir, exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex_script", gp, "-map", "[vout]", "-map", "[aout]",
                    "-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "17", "-r", str(FPS),
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", out], check=True)
    print(f"{out}  ({total:.1f}s, voice {vlen:.1f}s, {n} shots, {len(words)} words)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--only"); ap.add_argument("--outdir", default="clips")
    a = ap.parse_args()
    spec = json.load(open(a.spec))
    base = os.path.dirname(os.path.abspath(a.spec))
    for c in spec["clips"]:
        if not a.only or c["name"] == a.only:
            render(base, c, a.outdir)
