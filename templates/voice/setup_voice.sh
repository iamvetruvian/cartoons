#!/bin/bash
# One-time narration setup for the cartoon skill. Safe to re-run. Prints "Voice setup OK" when
# everything works (~3.5 GB of downloads with the GPU wheel, all free).
#   checks ffmpeg · builds the private Python env in ~/.cartoon-3d-short/venv
#   (numpy, scipy, kokoro-onnx, faster-whisper, onnxruntime-gpu on NVIDIA) ·
#   downloads the Kokoro voice (~340 MB) and Whisper small.en (~0.5 GB).
# Narration runs on the NVIDIA GPU when present (Kokoro auto-uses CUDA, Whisper device='cuda'),
# else on CPU (slower, same output contract).
# Adapted from the voice half of the user's faceless-shorts skill setup.sh (2026-11-14).
set -u
ok=1; say() { printf '%-12s %s\n' "$1" "$2"; }
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"
SKILL="$(cd "$(dirname "$0")/../.." && pwd)"; FH="${CARTOON_SHORTS_HOME:-$HOME/.cartoon-3d-short}"; VENV="$FH/venv"
export CARTOON_SHORTS_HOME="$FH"
for _nv in "$VENV"/lib/python*/site-packages/nvidia/*/lib; do [ -d "$_nv" ] && LD_LIBRARY_PATH="$_nv${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"; done
[ -n "${LD_LIBRARY_PATH:-}" ] && export LD_LIBRARY_PATH
if command -v ffmpeg >/dev/null && command -v ffprobe >/dev/null; then say ffmpeg ok; else say ffmpeg "MISSING (brew install ffmpeg · winget install ffmpeg · sudo apt install ffmpeg)"; ok=0; fi
PYBIN=""; for p in python3.11 python3.12 python3.10 python3 python "py -3"; do $p -c "import sys; assert sys.version_info >= (3, 10)" >/dev/null 2>&1 && PYBIN=$p && break; done   # 3.11 first: proven with kokoro-onnx + faster-whisper. Windows: python / py -3
mkdir -p "$FH"
if [ ! -x "$VENV/bin/python" ] && [ ! -x "$VENV/Scripts/python.exe" ]; then
  echo "building the Python env in $VENV (a few minutes)..."
  if command -v uv >/dev/null; then uv venv --python 3.11 "$VENV" >/dev/null 2>&1 || uv venv "$VENV" >/dev/null 2>&1
  elif [ -n "$PYBIN" ]; then $PYBIN -m venv "$VENV"; fi
fi
PY="$VENV/bin/python"; [ -x "$PY" ] || PY="$VENV/Scripts/python.exe"
CHECK="import numpy, scipy, kokoro_onnx, faster_whisper"
if [ -x "$PY" ]; then
  if ! "$PY" -c "$CHECK" 2>/dev/null; then
    if command -v uv >/dev/null; then uv pip install --python "$PY" -q numpy scipy kokoro-onnx faster-whisper >/dev/null 2>&1
    else "$PY" -m pip install -q --upgrade pip >/dev/null 2>&1; "$PY" -m pip install -q numpy scipy kokoro-onnx faster-whisper >/dev/null 2>&1; fi
  fi
  if "$PY" -c "$CHECK" 2>/dev/null; then say python-env "ok ($VENV)"; else say python-env "BROKEN: run  $PY -m pip install numpy scipy kokoro-onnx faster-whisper"; ok=0; fi
  GPUCHECK="import onnxruntime; assert 'CUDAExecutionProvider' in onnxruntime.get_available_providers()"
  if command -v nvidia-smi >/dev/null && nvidia-smi -L >/dev/null 2>&1 && ! "$PY" -c "$GPUCHECK" 2>/dev/null; then
    echo "installing onnxruntime-gpu + cuBLAS for CUDA narration (replaces the CPU onnxruntime wheel)..."
    if command -v uv >/dev/null; then uv pip uninstall --python "$PY" -q onnxruntime >/dev/null 2>&1; uv pip install --python "$PY" -q onnxruntime-gpu nvidia-cublas-cu12 >/dev/null 2>&1
    else "$PY" -m pip uninstall -q -y onnxruntime >/dev/null 2>&1; "$PY" -m pip install -q onnxruntime-gpu nvidia-cublas-cu12 >/dev/null 2>&1; fi
  fi
  if "$PY" -c "$GPUCHECK" 2>/dev/null; then say kokoro-gpu "ok (CUDA)"; else say kokoro-gpu "CPU only (no NVIDIA/CUDA: narration still works, slower)"; fi
  if "$PY" "$SKILL/templates/voice/voice.py" --download >/dev/null 2>&1; then say voice "ok (Kokoro, $FH/kokoro)"; else say voice "model download FAILED (check the internet connection, re-run)"; ok=0; fi
  if WHISPER_DEV=$("$PY" -c "
from faster_whisper import WhisperModel
import numpy as np
x = np.zeros(32000, np.float32)
try:
    m = WhisperModel('small.en', device='cuda', compute_type='float16'); list(m.transcribe(x)[0]); print('cuda')
except Exception:
    m = WhisperModel('small.en', device='cpu', compute_type='int8'); list(m.transcribe(x)[0]); print('cpu')
" 2>/dev/null); then say whisper "ok (small.en, $WHISPER_DEV)"; else say whisper "model/transcribe FAILED (re-run setup_voice.sh)"; ok=0; fi
else say python-env "MISSING: install Python 3.10+ (python.org) or uv (docs.astral.sh/uv)"; ok=0; fi
chmod +x "$SKILL"/templates/voice/*.sh "$SKILL"/templates/voice/py 2>/dev/null
[ $ok = 1 ] && echo "Voice setup OK" || { echo "Fix the MISSING items above, then run setup_voice.sh again."; exit 1; }
