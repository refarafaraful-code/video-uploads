"""Automated technical QC for a rendered Short. Visual review of frames is still required on top of this.

usage: python3 clipper/qc.py CLIP.mp4 [CLIP2.mp4 ...]   -> JSON per clip; exit 1 if any clip fails

status: pass | pass_with_notes (minor notes) | needs_review (black/frozen/silent stretches, duplicate of a
registered clip) | fail (unreadable, wrong format, no audio, bad duration). Only pass / pass_with_notes may be delivered.

This is TECHNICAL QC only. It does not judge caption accuracy, crop/framing, whether the hook and payoff land, or
edit meaning - those need the frame review described in CLAUDE.md.
"""
import json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import registry


def run(args):
    return subprocess.run(args, capture_output=True, text=True)


def qc(path, reg=None):
    errors, review, warnings, info = [], [], [], {}
    p = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels",
             "-of", "json", path])
    if p.returncode:
        return {"file": path, "status": "fail", "errors": ["ffprobe cannot read file: " + p.stderr.strip()[:200]]}
    d = json.loads(p.stdout)
    v = [s for s in d["streams"] if s["codec_type"] == "video"]
    a = [s for s in d["streams"] if s["codec_type"] == "audio"]
    dur = float(d["format"]["duration"])
    info["duration_s"] = round(dur, 2)
    if not v:
        errors.append("no video stream")
    else:
        v = v[0]
        num, den = map(int, v["r_frame_rate"].split("/"))
        info.update(codec=v["codec_name"], width=v["width"], height=v["height"], fps=round(num / den, 2))
        if (v["width"], v["height"]) != (1080, 1920):
            errors.append(f"resolution {v['width']}x{v['height']} (expected 1080x1920)")
        if abs(num / den - 30) > 0.5:
            warnings.append(f"fps {num / den:.2f}")
    if not a:
        errors.append("no audio stream")
    if not 8 <= dur <= 180:
        errors.append(f"duration {dur:.1f}s outside Shorts range")
    elif dur > 60:
        warnings.append(f"duration {dur:.1f}s > 60s (allowed, but long for a Short)")

    # full decode: catches corrupt frames; detectors for black / frozen video and silent audio
    r = run(["ffmpeg", "-v", "info", "-nostats", "-i", path, "-vf", "blackdetect=d=0.4:pic_th=0.97,freezedetect=n=0.002:d=1.5",
             "-af", "silencedetect=n=-45dB:d=1.5,ebur128", "-f", "null", "-"])
    log = r.stderr
    if r.returncode:
        errors.append("decode error")
    if re.search(r"(error while decoding|corrupt|Invalid NAL)", log, re.I):
        errors.append("decoder reported corrupt data")
    blacks = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", log)
    freezes = re.findall(r"freeze_start: ([\d.]+)", log)
    silences = re.findall(r"silence_start: ([\d.]+)", log)
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", log)
    info.update(black_segments=len(blacks), freeze_segments=len(freezes), silent_segments=len(silences))
    if blacks:
        review.append("black frames at " + ", ".join(f"{float(s):.1f}-{float(e):.1f}s" for s, e in blacks[:5]))
    if freezes:
        review.append("frozen video at " + ", ".join(f"{float(s):.1f}s" for s in freezes[:5]))
    if silences:
        review.append("silence >1.5s at " + ", ".join(f"{float(s):.1f}s" for s in silences[:5]))
    if reg is not None:
        digest = registry.sha256(path)
        info["sha256"] = digest
        for c in reg["clips"]:
            for kind, f in c.get("files", {}).items():
                if f.get("sha256") == digest and os.path.abspath(path) != os.path.abspath(os.path.join(registry.ROOT, f["path"])):
                    review.append(f"identical to registered clip {c['id']} ({kind}) - duplicate output")
    if lufs:
        info["loudness_lufs"] = float(lufs[-1])
        if not -14 <= float(lufs[-1]) <= -6:
            warnings.append(f"loudness {lufs[-1]} LUFS (target about -9)")
    status = "fail" if errors else "needs_review" if review else "pass_with_notes" if warnings else "pass"
    return {"file": path, "status": status, "errors": errors, "needs_review": review, "warnings": warnings, **info}


if __name__ == "__main__":
    try:
        reg = registry.load()
    except FileNotFoundError:
        reg = None
    results = [qc(f, reg) for f in sys.argv[1:]]
    print(json.dumps(results, indent=1))
    sys.exit(1 if any(r["status"] in ("fail", "needs_review") for r in results) else 0)
