"""Production registry: duplicate detection and registry/filesystem reconciliation.

usage:
  python3 clipper/registry.py releases            # classify every release asset: processed / possible duplicate / new
  python3 clipper/registry.py check FILE          # is this local video already a registered source? (hash, audio fingerprint, metadata)
  python3 clipper/registry.py register-source FILE --id ID --title T --creator C [--filename ORIGINAL --tag TAG --asset-id N --project DIR]
  python3 clipper/registry.py hash FILE           # sha256 + basic probe
  python3 clipper/registry.py verify              # registry vs files on disk (missing, changed, unregistered)
  python3 clipper/registry.py status              # short summary

Other scripts import load()/save(); save() writes atomically so an interrupted run never truncates the registry.
"""
import argparse, hashlib, json, os, subprocess, sys, tempfile
import numpy as np
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "production_data", "production_registry.json")
FP_DIR = os.path.join(ROOT, "production_data", "fingerprints")
REPO = "refarafaraful-code/video-uploads"
FP_ITEM_S = 0.1242          # chromaprint: one 32-bit item per ~0.124 s of audio
FP_MIN_OVERLAP_S = 20       # shared audio needed to call it the same footage
FP_MAX_BER = 0.30           # mean bit error rate on the aligned overlap (unrelated audio is ~0.5)
FP_MIN_COVER = 0.5          # ...and it must cover this share of the candidate; less (e.g. a shared outro song) -> review


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load():
    with open(REGISTRY) as f:
        return json.load(f)


def save(reg):
    reg["updated_at"] = now()
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(REGISTRY), suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(reg, f, indent=2, ensure_ascii=False)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, REGISTRY)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
                          "-of", "json", path], capture_output=True, text=True, check=True).stdout
    d = json.loads(out)
    v = next((s for s in d["streams"] if s["codec_type"] == "video"), {})
    num, den = map(int, v.get("r_frame_rate", "0/1").split("/"))
    return {"duration_s": round(float(d["format"]["duration"]), 3), "width": v.get("width"), "height": v.get("height"),
            "fps": round(num / den, 3) if den else None,
            "has_audio": any(s["codec_type"] == "audio" for s in d["streams"])}


def fingerprint(path):
    """chromaprint audio fingerprint as uint32 array (empty if the file has no audio)"""
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vn", "-ac", "1", "-ar", "11025", "-f", "chromaprint",
                        "-fp_format", "raw", "-"], capture_output=True)
    return np.frombuffer(r.stdout, dtype="<u4") if r.returncode == 0 else np.zeros(0, dtype="<u4")


def fp_match(a, b):
    """best alignment of fingerprint a inside/over b -> (overlap_s, bit_error_rate, offset_s of a's start in b)"""
    if len(a) < 10 or len(b) < 10:
        return 0.0, 1.0, 0.0
    pos = {}
    for j, v in enumerate(b):
        pos.setdefault(int(v), []).append(j)
    votes = {}
    for i, v in enumerate(a):           # exact 32-bit hits vote for an offset; survives most re-encodes
        for j in pos.get(int(v), ())[:50]:
            votes[j - i] = votes.get(j - i, 0) + 1
    best = (0.0, 1.0, 0.0)
    win = 40                            # ~5 s windows: only windows that really match count as shared footage
    for off, _ in sorted(votes.items(), key=lambda kv: -kv[1])[:5]:
        i0, j0 = max(0, -off), max(0, off)
        n = min(len(a) - i0, len(b) - j0)
        if n < win:
            continue
        bits = np.unpackbits(np.bitwise_xor(a[i0:i0 + n], b[j0:j0 + n]).view(np.uint8)).reshape(n, 32).mean(1)
        w = bits[:n // win * win].reshape(-1, win).mean(1)
        good = w <= FP_MAX_BER
        if not good.any():
            continue
        overlap = good.sum() * win * FP_ITEM_S
        if overlap > best[0]:
            best = (overlap, float(w[good].mean()), off * FP_ITEM_S)
    return best


def load_fp(src):
    f = src.get("audio_fingerprint")
    if not f:
        return None
    return np.fromfile(os.path.join(ROOT, f["path"]), dtype="<u4")


def classify(reg, digest=None, size=None, duration=None, height=None, name=None, fp=None):
    """-> (status, source_id, reason); status is processed | possible_duplicate | new
    processed: byte-identical, or the same audio content over >= FP_MIN_OVERLAP_S (re-encode, rename, trim)"""
    for s in reg["sources"]:
        if digest and s.get("sha256") == digest:
            return "processed", s["id"], "identical sha256"
    for c in reg["clips"]:
        if digest and any(f.get("sha256") == digest for f in c.get("files", {}).values()):
            return "processed", c["source_id"], f"this file is our own exported clip {c['id']}"
    if fp is not None and len(fp):
        partial = None
        for s in reg["sources"]:
            sfp = load_fp(s)
            if sfp is None:
                continue
            overlap, ber, off = fp_match(fp, sfp)
            if overlap >= FP_MIN_OVERLAP_S and ber <= FP_MAX_BER:
                desc = f"{overlap:.0f}s of identical audio at {off:+.0f}s in the source (bit error {ber:.2f})"
                if overlap >= FP_MIN_COVER * len(fp) * FP_ITEM_S:
                    return "processed", s["id"], f"same audio content: {desc} - re-encoded/renamed/trimmed copy"
                partial = partial or (s["id"], f"partly shared audio: {desc}, under {FP_MIN_COVER:.0%} of this file "
                                                f"(shared music? compilation?) - inspect before processing")
        if partial:
            return "possible_duplicate", *partial
    for s in reg["sources"]:
        reasons = []
        if name and name == s.get("filename"):
            reasons.append("same filename")
        if duration and s.get("duration_s") and abs(duration - s["duration_s"]) < 1.0:
            reasons.append(f"same duration ({duration:.1f}s)" + (" and height" if height == s.get("height") else ""))
        if reasons:
            return "possible_duplicate", s["id"], ", ".join(reasons) + " but different hash (re-encode/trim?) - inspect before processing"
    missing = [s["id"] for s in reg["sources"] if not s.get("audio_fingerprint")]
    if fp is not None and not len(fp):
        return "possible_duplicate", None, "file has no usable audio, so content could not be compared - inspect visually"
    if missing:
        return "possible_duplicate", None, f"no fingerprint stored for {missing}; content not compared - inspect"
    return "new", None, ""


def cmd_releases(reg):
    out = subprocess.run(["gh", "api", f"repos/{REPO}/releases", "--paginate"], capture_output=True, text=True, check=True).stdout
    for rel in json.loads(out):
        for a in rel["assets"]:
            digest = (a.get("digest") or "").removeprefix("sha256:") or None
            st, sid, why = classify(reg, digest=digest, size=a["size"], name=a["name"])
            print(f"{st:18} tag={rel['tag_name']:<10} asset={a['id']}  {a['name']}  ({a['size'] / 1e6:.0f} MB)"
                  + (f"  -> {sid}: {why}" if sid else ""))


def cmd_check(reg, path):
    p = probe(path)
    st, sid, why = classify(reg, digest=sha256(path), duration=p["duration_s"], height=p["height"],
                            name=os.path.basename(path), fp=fingerprint(path))
    print(json.dumps({"status": st, "source_id": sid, "reason": why, **p}, indent=1))
    return st


def save_fp(source_id, fp):
    os.makedirs(FP_DIR, exist_ok=True)
    rel = os.path.join("production_data", "fingerprints", f"{source_id}.fp")
    fp.astype("<u4").tofile(os.path.join(ROOT, rel))
    return {"path": rel, "method": "chromaprint raw, mono 11025 Hz", "items": int(len(fp)), "item_s": FP_ITEM_S}


def cmd_register_source(reg, a):
    """add a new source (status in_progress) after verifying it is not already registered"""
    if any(s["id"] == a.id for s in reg["sources"]):
        sys.exit(f"source id {a.id} already exists")
    p, digest, fp = probe(a.file), sha256(a.file), fingerprint(a.file)
    st, sid, why = classify(reg, digest=digest, duration=p["duration_s"], height=p["height"],
                            name=a.filename or os.path.basename(a.file), fp=fp)
    if st != "new" and not a.allow_reprocess:
        sys.exit(f"refusing to register: {st} ({sid}: {why}). Use --allow-reprocess only with the owner's explicit approval.")
    reg["sources"].append({"id": a.id, "title": a.title, "creator": a.creator, "campaign": a.campaign,
                           "filename": a.filename or os.path.basename(a.file), "local_path": os.path.relpath(a.file, ROOT),
                           "release": {"tag": a.tag, "asset_id": a.asset_id},
                           "sha256": digest, "size_bytes": os.path.getsize(a.file), "duration_s": p["duration_s"],
                           "width": p["width"], "height": p["height"], "fps": p["fps"],
                           "audio_fingerprint": save_fp(a.id, fp) if len(fp) else None,
                           "project_dir": a.project, "first_processed": now()[:10], "runs": [], "status": "in_progress",
                           "candidates": [], "notes": f"duplicate check at registration: {st} {why}".strip()})
    save(reg)
    print(f"registered {a.id} ({st})")


def cmd_verify(reg):
    problems, known = 0, set()
    for s in reg["sources"]:
        if not s.get("audio_fingerprint"):
            print(f"NO-FP    {s['id']} has no audio fingerprint (trimmed/re-encoded copies of it cannot be detected)"); problems += 1
        elif not os.path.exists(os.path.join(ROOT, s["audio_fingerprint"]["path"])):
            print(f"MISSING  {s['id']} fingerprint file {s['audio_fingerprint']['path']}"); problems += 1
    session_only = 0
    for c in reg["clips"]:
        for kind, f in c.get("files", {}).items():
            if not f.get("in_repo"):
                session_only += 1
                continue
            path = os.path.join(ROOT, f["path"])
            known.add(os.path.normpath(path))
            if not os.path.exists(path):
                print(f"MISSING  {c['id']} {kind}: {f['path']}"); problems += 1
            elif f.get("sha256") and sha256(path) != f["sha256"]:
                print(f"CHANGED  {c['id']} {kind}: {f['path']}"); problems += 1
    for d in os.listdir(ROOT):
        if d.startswith("shorts-") and os.path.isdir(os.path.join(ROOT, d)):
            for fn in sorted(os.listdir(os.path.join(ROOT, d))):
                p = os.path.normpath(os.path.join(ROOT, d, fn))
                if fn.endswith(".mp4") and p not in known:
                    print(f"UNREGISTERED  {d}/{fn}"); problems += 1
    for c in reg["clips"]:
        if c["status"] in ("completed", "scheduled", "published") and c.get("qc", {}).get("status") not in ("pass", "pass_with_notes"):
            print(f"QC-GAP   {c['id']} is {c['status']} without a passing QC record"); problems += 1
    if session_only:
        print(f"note: {session_only} file record(s) are session-only copies (not in the repo) and were not checked")
    print("registry consistent with files" if not problems else f"{problems} problem(s)")
    return problems


def cmd_status(reg):
    print(f"registry updated {reg['updated_at']}")
    for s in reg["sources"]:
        n = sum(1 for c in reg["clips"] if c["source_id"] == s["id"])
        print(f"  {s['id']:<16} {s['status']:<12} {n} clips  {s['filename']}")
    by = {}
    for c in reg["clips"]:
        by[c["status"]] = by.get(c["status"], 0) + 1
    print("  clips by status:", by)


if __name__ == "__main__":
    reg = load()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "register-source":
        ap = argparse.ArgumentParser(prog="registry.py register-source")
        ap.add_argument("file"); ap.add_argument("--id", required=True); ap.add_argument("--title", required=True)
        ap.add_argument("--creator", required=True); ap.add_argument("--campaign"); ap.add_argument("--tag")
        ap.add_argument("--asset-id", type=int); ap.add_argument("--project"); ap.add_argument("--allow-reprocess", action="store_true")
        ap.add_argument("--filename", help="original filename (release asset name); defaults to the local file name")
        cmd_register_source(reg, ap.parse_args(sys.argv[2:]))
    elif cmd == "releases":
        cmd_releases(reg)
    elif cmd == "check":
        sys.exit(0 if cmd_check(reg, sys.argv[2]) == "new" else 3)
    elif cmd == "hash":
        print(json.dumps({"sha256": sha256(sys.argv[2]), **probe(sys.argv[2])}, indent=1))
    elif cmd == "verify":
        sys.exit(1 if cmd_verify(reg) else 0)
    else:
        cmd_status(reg)
