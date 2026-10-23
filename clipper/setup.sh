#!/usr/bin/env bash
# One-time setup for a fresh cloud session. Run from anywhere: bash clipper/setup.sh
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

pip install -q "yt-dlp[default]" sherpa-onnx soundfile scipy numpy "opencv-python-headless<5" pillow

# fonts used by the captions/title (libass looks them up via fontconfig)
mkdir -p ~/.fonts && cp "$HERE"/fonts/*.ttf ~/.fonts/ && fc-cache -f >/dev/null

# speech-to-text model (HuggingFace is blocked here; GitHub releases work)
if [ ! -f "$HERE/models/parakeet/encoder.int8.onnx" ]; then
  mkdir -p "$HERE/models/parakeet"
  curl -sSLf https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8.tar.bz2 \
    | tar xj -C "$HERE/models/parakeet" --strip-components=1
fi

# sound-effect kit + music beds are synthesized (deterministic)
[ -f "$HERE/sfx/bed_hype.wav" ] || python3 -I "$HERE/make_sfx.py"
echo "setup done"
