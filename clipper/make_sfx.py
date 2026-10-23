"""Synthesize the sound-effect kit used by make_clip.py into ./sfx/*.wav"""
import os
import numpy as np
from scipy import signal
from scipy.io import wavfile

SR = 48000
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)


def save(name, x):
    x = np.atleast_2d(x)
    if x.shape[0] != 2:
        x = np.vstack([x, x])
    x = x / (np.abs(x).max() + 1e-9) * 0.95
    wavfile.write(os.path.join(OUT, name + ".wav"), SR, (x.T * 32767).astype(np.int16))


def t_(d):
    return np.arange(int(d * SR)) / SR


def sweep_bp(noise, f0, f1, q=2.0, blocks=200):
    """band-pass noise with a cutoff that glides from f0 to f1"""
    out = np.zeros_like(noise)
    n = len(noise)
    edges = np.linspace(0, n, blocks + 1).astype(int)
    zi = None
    for i in range(blocks):
        f = f0 * (f1 / f0) ** (i / blocks)
        b, a = signal.iirpeak(min(f, SR / 2 - 100), q, fs=SR)
        if zi is None:
            zi = signal.lfilter_zi(b, a) * 0
        out[edges[i]:edges[i + 1]], zi = signal.lfilter(b, a, noise[edges[i]:edges[i + 1]], zi=zi)
    return out


def env(n, attack, release_shape=4.0):
    e = np.ones(n)
    a = int(attack * n)
    e[:a] = np.linspace(0, 1, a) ** 2
    e[a:] = np.linspace(1, 0, n - a) ** release_shape
    return e


# whoosh: swept noise, panned left->right
d = 0.55
nz = rng.standard_normal(int(d * SR))
w = sweep_bp(nz, 300, 5000, q=1.2) * env(len(nz), 0.65, 2.5)
pan = np.linspace(0, 1, len(w))
save("whoosh", np.vstack([w * np.cos(pan * np.pi / 2), w * np.sin(pan * np.pi / 2)]))

# rewind: reversed, higher whoosh with pitch flutter
nz = rng.standard_normal(int(0.7 * SR))
r = sweep_bp(nz, 6000, 400, q=3) * env(len(nz), 0.2, 1.5)
r *= 1 + 0.5 * np.sin(2 * np.pi * 18 * t_(0.7))
save("rewind", r)

# impact: pitch-dropping sub + noise crack, soft clipped
tt = t_(1.4)
f = 40 + 110 * np.exp(-tt * 9)
sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 3.2)
crack = rng.standard_normal(len(tt)) * np.exp(-tt * 40)
crack = signal.sosfilt(signal.butter(2, 2500, "low", fs=SR, output="sos"), crack)
save("impact", np.tanh(2.5 * (sub + 0.6 * crack)))

# bass drop: long 808 glide
tt = t_(2.0)
f = 30 + 70 * np.exp(-tt * 2.5)
save("bassdrop", np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.4)))

# riser: noise + rising saw, ends abruptly (place so it ends on the payoff)
tt = t_(2.5)
nz = sweep_bp(rng.standard_normal(len(tt)), 200, 8000, q=0.8)
saw = signal.sawtooth(2 * np.pi * np.cumsum(110 * 2 ** (tt * 1.6)) / SR)
saw = signal.sosfilt(signal.butter(2, 3000, "low", fs=SR, output="sos"), saw)
save("riser", (nz * 0.8 + 0.25 * saw) * (tt / tt[-1]) ** 2.2)

# pop: short click for word emphasis / text slam
tt = t_(0.12)
save("pop", np.sin(2 * np.pi * (900 - 5000 * tt) * tt) * np.exp(-tt * 45))

# dark cinematic bed, 32s loop: minor pad + slow sub pulse at 80 bpm
D = 32.0
tt = t_(D)
pad = np.zeros_like(tt)
chords = [[57, 60, 64], [53, 57, 60], [55, 59, 62], [52, 55, 59]]  # Am F G Em
seg = D / len(chords)
for i, ch in enumerate(chords):
    m = (tt >= i * seg) & (tt < (i + 1) * seg)
    lt = tt[m] - i * seg
    e = np.minimum(1, lt / 1.5) * np.minimum(1, (seg - lt) / 1.5)
    for note in ch:
        fr = 440 * 2 ** ((note - 12 - 69) / 12)
        for det in (-0.15, 0.15):
            pad[m] += signal.sawtooth(2 * np.pi * fr * (1 + det / 100) * lt) * e
pad = signal.sosfilt(signal.butter(2, 900, "low", fs=SR, output="sos"), pad)
beat = 60 / 80
ph = (tt % beat) / beat
sub = np.sin(2 * np.pi * 45 * tt) * np.exp(-ph * 6)
tick = signal.sosfilt(signal.butter(2, 6000, "high", fs=SR, output="sos"), rng.standard_normal(len(tt))) * np.exp(-((tt + beat / 2) % beat) / beat * 40) * 0.15
bed = 0.5 * pad / np.abs(pad).max() + 0.6 * sub + tick
lfo = 0.5 + 0.5 * np.sin(2 * np.pi * tt / 8)
save("bed", np.vstack([bed * (0.8 + 0.2 * lfo), bed * (1 - 0.2 * lfo)]))
print("sfx written to", OUT, sorted(os.listdir(OUT)))

# ---- v2 kit
# glitch: stuttered bit-crushed noise bursts
tt = t_(0.35)
g = rng.standard_normal(len(tt))
g = np.round(g * 3) / 3
gate = (np.floor(tt * 40) % 3 != 1).astype(float)
g = g * gate * np.exp(-tt * 6)
g += 0.6 * signal.square(2 * np.pi * 180 * tt) * gate * np.exp(-tt * 8)
save("glitch", signal.sosfilt(signal.butter(2, [300, 7000], "band", fs=SR, output="sos"), g))

# boom: deep "vine-boom" style hit with a long tail
tt = t_(2.2)
f = 48 + 60 * np.exp(-tt * 14)
b = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tt * 1.8)
b += 0.3 * np.sin(2 * np.pi * np.cumsum(f * 2.01) / SR) * np.exp(-tt * 4)
click = rng.standard_normal(len(tt)) * np.exp(-tt * 120)
save("boom", np.tanh(3 * (b + 0.5 * click)))

# beep: censor tone
save("beep", 0.8 * np.sin(2 * np.pi * 1000 * t_(1.0)))

# swoosh up for text entrances (short, bright)
nz = rng.standard_normal(int(0.3 * SR))
save("swoosh", sweep_bp(nz, 1500, 9000, q=2) * env(len(nz), 0.7, 2))


def drums(D, bpm, kick_pattern, hat_div=2, clap=True):
    tt = t_(D)
    out = np.zeros_like(tt)
    beat = 60 / bpm
    kick = np.sin(2 * np.pi * np.cumsum(45 + 120 * np.exp(-t_(0.4) * 30)) / SR) * np.exp(-t_(0.4) * 9)
    hat = signal.sosfilt(signal.butter(4, 8000, "high", fs=SR, output="sos"), rng.standard_normal(int(0.05 * SR))) * np.exp(-t_(0.05) * 90)
    clp = signal.sosfilt(signal.butter(2, [900, 4000], "band", fs=SR, output="sos"), rng.standard_normal(int(0.2 * SR))) * np.exp(-t_(0.2) * 25)

    def put(x, at, v):
        i = int(at * SR)
        j = min(len(out), i + len(x))
        out[i:j] += v * x[:j - i]
    n = int(D / beat)
    for i in range(n):
        if kick_pattern[i % len(kick_pattern)]:
            put(kick, i * beat, 1.0)
        if clap and i % 2 == 1:
            put(clp, i * beat, 0.5)
        for h in range(hat_div):
            put(hat, (i + h / hat_div) * beat, 0.25 if h else 0.35)
    return out


# fun bed: bouncy major plucks over light drums, 112 bpm
D, bpm = 34.3, 112
tt = t_(D)
beat = 60 / bpm
mel = [72, 76, 79, 76, 74, 77, 81, 77, 72, 76, 79, 84, 79, 76, 74, 71]
pl = np.zeros_like(tt)
step = beat / 2
for i in range(int(D / step)):
    note = mel[i % len(mel)] - 12 * (i // 64 % 2 == 1)
    fr = 440 * 2 ** ((note - 69) / 12)
    lt = t_(0.3)
    x = (signal.square(2 * np.pi * fr * lt, 0.3) * 0.4 + np.sin(2 * np.pi * fr * lt)) * np.exp(-lt * 14)
    a = int(i * step * SR)
    pl[a:a + len(x)] += x[:len(pl) - a]
bass = np.zeros_like(tt)
for i in range(int(D / beat)):
    root = [48, 45, 41, 43][(i // 4) % 4]
    fr = 440 * 2 ** ((root - 69) / 12)
    lt = t_(beat)
    a = int(i * beat * SR)
    x = np.sin(2 * np.pi * fr * lt) * np.exp(-lt * 3)
    bass[a:a + len(x)] += x[:len(bass) - a]
fun = 0.35 * pl + 0.6 * bass + 0.7 * drums(D, bpm, [1, 0, 1, 0, 1, 0, 1, 1])
save("bed_fun", fun)

# hype bed: dark trap, 140 bpm half-time 808s + rolling hats
D, bpm = 34.3, 140
tt = t_(D)
beat = 60 / bpm
sub = np.zeros_like(tt)
for i in range(0, int(D / beat), 2):
    root = [38, 38, 41, 36][(i // 8) % 4]
    fr = 440 * 2 ** ((root - 69) / 12)
    lt = t_(beat * 2)
    a = int(i * beat * SR)
    x = np.tanh(2 * np.sin(2 * np.pi * fr * lt) * np.exp(-lt * 1.2))
    sub[a:a + len(x)] += x[:len(sub) - a]
pad = np.zeros_like(tt)
for note in (62, 65, 69):
    pad += signal.sawtooth(2 * np.pi * 440 * 2 ** ((note - 12 - 69) / 12) * tt)
pad = signal.sosfilt(signal.butter(2, 700, "low", fs=SR, output="sos"), pad) * (0.6 + 0.4 * np.sin(2 * np.pi * tt / 4))
hype = 0.8 * sub + 0.15 * pad / np.abs(pad).max() + 0.6 * drums(D, bpm, [1, 0, 0, 0, 0, 0, 1, 0], hat_div=4)
save("bed_hype", hype)
print("v2 kit ok")
