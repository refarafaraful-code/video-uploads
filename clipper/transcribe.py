"""Transcribe a video to word-level timestamps (Parakeet via sherpa-onnx).

usage: python3 transcribe.py VIDEO OUT.json [--model DIR]
"""
import argparse, json, subprocess, tempfile, os
import numpy as np
import soundfile as sf
import sherpa_onnx

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("out")
ap.add_argument("--model", default=os.environ.get("PARAKEET_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "parakeet")))
a = ap.parse_args()

with tempfile.TemporaryDirectory() as td:
    wav = os.path.join(td, "a.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.video, "-ac", "1", "-ar", "16000", wav], check=True)
    audio, sr = sf.read(wav, dtype="float32")

m = a.model
rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{m}/encoder.int8.onnx", decoder=f"{m}/decoder.int8.onnx",
    joiner=f"{m}/joiner.int8.onnx", tokens=f"{m}/tokens.txt",
    model_type="nemo_transducer", num_threads=os.cpu_count())

# chunk at the quietest point near every ~25s so words aren't split
CH, SEARCH = 25 * sr, 3 * sr
win = sr // 50
energy = np.convolve(audio ** 2, np.ones(win) / win, mode="same")
bounds, pos = [0], 0
while pos + CH < len(audio):
    lo, hi = pos + CH - SEARCH, min(pos + CH + SEARCH, len(audio))
    pos = lo + int(np.argmin(energy[lo:hi]))
    bounds.append(pos)
bounds.append(len(audio))

words = []
for s, e in zip(bounds, bounds[1:]):
    st = rec.create_stream(); st.accept_waveform(sr, audio[s:e]); rec.decode_stream(st)
    r = st.result
    off = s / sr
    for tok, t in zip(r.tokens, r.timestamps):
        t += off
        if tok.startswith(" ") or not words:
            words.append({"w": tok.strip(), "s": round(t, 3), "e": round(t + 0.08, 3)})
        else:
            words[-1]["w"] += tok
            words[-1]["e"] = round(t + 0.08, 3)
words = [w for w in words if w["w"]]
# word ends at next word's start when contiguous
for w, n in zip(words, words[1:]):
    w["e"] = round(min(max(w["e"], n["s"] - 0.02), w["s"] + 1.2) if n["s"] - w["s"] < 1.2 else w["e"] + 0.25, 3)
if words:
    words[-1]["e"] += 0.25

json.dump({"duration": len(audio) / sr, "words": words}, open(a.out, "w"), indent=0)
# readable transcript, a line per pause
line, last = [], None
for w in words:
    if last is not None and w["s"] - last > 0.6 and line:
        print(f"[{line[0]['s']:7.2f}] " + " ".join(x["w"] for x in line)); line = []
    line.append(w); last = w["e"]
if line:
    print(f"[{line[0]['s']:7.2f}] " + " ".join(x["w"] for x in line))
