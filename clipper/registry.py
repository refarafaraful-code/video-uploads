"""Production registry: duplicate detection and registry/filesystem reconciliation.

usage:
  python3 clipper/registry.py releases            # classify every release asset: processed / possible duplicate / new
  python3 clipper/registry.py check FILE          # is this local video already a registered source?
  python3 clipper/registry.py hash FILE           # sha256 + basic probe
  python3 clipper/registry.py verify              # registry vs files on disk (missing, changed, unregistered)
  python3 clipper/registry.py status              # short summary

Other scripts import load()/save(); save() writes atomically so an interrupted run never truncates the registry.
"""
import hashlib, json, os, subprocess, sys, tempfile
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "production_data", "production_registry.json")
REPO = "refarafaraful-code/video-uploads"


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


def classify(reg, digest=None, size=None, duration=None, height=None, name=None):
    """-> (status, source_id, reason); status is processed | possible_duplicate | new"""
    for s in reg["sources"]:
        if digest and s.get("sha256") == digest:
            return "processed", s["id"], "identical sha256"
    for s in reg["sources"]:
        reasons = []
        if name and name == s.get("filename"):
            reasons.append("same filename")
        if duration and s.get("duration_s") and abs(duration - s["duration_s"]) < 1.0:
            reasons.append(f"same duration ({duration:.1f}s)" + (" and height" if height == s.get("height") else ""))
        if reasons:
            return "possible_duplicate", s["id"], ", ".join(reasons) + " but different hash (re-encode/trim?) - inspect before processing"
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
    st, sid, why = classify(reg, digest=sha256(path), duration=p["duration_s"], height=p["height"], name=os.path.basename(path))
    print(json.dumps({"status": st, "source_id": sid, "reason": why, **p}, indent=1))


def cmd_verify(reg):
    problems, known = 0, set()
    for c in reg["clips"]:
        for kind, f in c.get("files", {}).items():
            if not f.get("in_repo"):
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
    if cmd == "releases":
        cmd_releases(reg)
    elif cmd == "check":
        cmd_check(reg, sys.argv[2])
    elif cmd == "hash":
        print(json.dumps({"sha256": sha256(sys.argv[2]), **probe(sys.argv[2])}, indent=1))
    elif cmd == "verify":
        sys.exit(1 if cmd_verify(reg) else 0)
    else:
        cmd_status(reg)
