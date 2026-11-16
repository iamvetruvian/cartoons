"""Render a cartoon short's narration with the vendored Kokoro + Whisper setup.

  templates/voice/py templates/voice/render_narration.py lines.txt <project>/voice/ --dur 67.5
  templates/voice/py templates/voice/render_narration.py lines.json <project>/voice/ --voice bm_fable --speed 1.05
  templates/voice/py templates/voice/render_narration.py lines.txt <project>/voice/ --audio my_take.m4a
  templates/voice/py templates/voice/render_narration.py lines.txt <project>/voice/ --estimate
  templates/voice/py templates/voice/render_narration.py --list

lines.txt = the approved script, one CUT per line (blank lines and # comments skipped).
lines.json = [{"text": "...", "gap": 0.4}, ...] for per-line pauses. Write numbers the way they're SAID.
A line is a CUT, not a sentence: sentences may run across lines; each sentence is spoken in one pass.

Outputs in <project>/voice/: voice.wav (48 kHz mono, exactly --dur when given), words.json [{w,s,e}]
(the picture and the mix are timed to it), plus words.txt + lines.json to check and hand-fix against.
--audio: your own recording becomes voice.wav; Whisper rebuilds the timings from it (Whisper required).
--estimate: timing preview with no voice yet (stdlib only, no voice.wav); re-run without it later.
Run setup_voice.sh once per computer first; always run this through the `py` shim (the voice venv).
"""
import argparse
import json
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
NEED = ["numpy", "scipy", "kokoro_onnx", "faster_whisper"]


def read_lines(path):
    p = Path(path)
    if p.suffix == ".json":
        out = []
        for e in json.loads(p.read_text(encoding="utf-8")):
            e = {"text": e} if isinstance(e, str) else dict(e)
            out.append({"text": e["text"], **({"gap": e["gap"]} if "gap" in e else {})})
        return out
    lines = []
    for raw in p.read_text(encoding="utf-8").splitlines():
        t = raw.strip()
        if t and not t.startswith("#"):
            lines.append({"text": t})
    return lines


def read_mono_int16(path):
    with wave.open(str(path), "rb") as w:
        n, ch, sw, sr = w.getnframes(), w.getnchannels(), w.getsampwidth(), w.getframerate()
        raw = w.readframes(n)
    assert sw == 2, sw
    import numpy as np
    return np.frombuffer(raw, "<i2").astype(np.float64).reshape(-1, ch).mean(1) / 32768.0, sr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lines", nargs="?")
    ap.add_argument("voicedir", nargs="?")
    ap.add_argument("--voice", default="bm_george")
    ap.add_argument("--speed", type=float, default=1.15)  # standard narration pace for every video
    ap.add_argument("--lead", type=float, default=0.4)
    ap.add_argument("--gap", type=float, default=0.32)
    ap.add_argument("--outro", type=float, default=0.9)
    ap.add_argument("--dur", type=float, default=None, help="pad/trim voice.wav to exactly this many seconds")
    ap.add_argument("--audio", default=None, help="your own recording (becomes voice.wav, Whisper times it)")
    ap.add_argument("--estimate", action="store_true", help="timing preview only, no voice.wav")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()
    if a.list:
        subprocess.run([sys.executable, str(HERE / "voice.py"), "--list"], check=True)
        return
    if not a.lines or not a.voicedir:
        ap.error("lines file and voice dir missing")
    missing = [m for m in NEED if not _importable(m)]
    if missing and not (a.estimate and set(missing) <= {"kokoro_onnx", "faster_whisper"}):
        raise SystemExit(f"missing in this Python ({sys.executable}): {', '.join(missing)}.\n"
                         f"Run templates/voice/setup_voice.sh once, then re-run through templates/voice/py.")
    lines = read_lines(a.lines)
    if not lines:
        raise SystemExit(f"no lines in {a.lines}")
    script = {"voice": a.voice, "speed": a.speed, "lead": a.lead, "outro": a.outro, "gap": a.gap, "lines": lines}
    vd = Path(a.voicedir)
    vd.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="narration-") as tmp:
        T = Path(tmp)
        (T / "script.json").write_text(json.dumps(script, indent=1), encoding="utf-8")
        if a.estimate:
            subprocess.run([sys.executable, str(HERE / "estimate.py"), str(T)], check=True)
        else:
            if not a.audio:
                subprocess.run([sys.executable, str(HERE / "voice.py"), str(T)], check=True)
            cmd = [sys.executable, str(HERE / "words.py"), str(T)]
            if a.audio:
                cmd += ["--audio", a.audio]
            subprocess.run(cmd, check=True)
        data = json.loads((T / "data/words.json").read_text(encoding="utf-8"))
        words = [{"w": w["w"], "s": w["s"], "e": w["e"]} for w in data]
        (vd / "words.json").write_text(json.dumps(words, indent=1), encoding="utf-8")
        if (T / "data/words.txt").exists():  # estimate mode writes no words.txt (no Whisper run)
            (vd / "words.txt").write_text((T / "data/words.txt").read_text(encoding="utf-8"), encoding="utf-8")
        (vd / "lines.json").write_text((T / "data/lines.json").read_text(encoding="utf-8"), encoding="utf-8")
        if not a.estimate:
            import numpy as np
            from scipy import signal as spsig
            x, sr = read_mono_int16(T / "data/narration.wav")
            assert sr == 24000, sr
            y = spsig.resample_poly(x, 2, 1).astype(np.float64)  # exact 2x to 48 kHz
            y = y / (np.abs(y).max() + 1e-9) * 0.89              # peak ~-1 dBFS; the mix keeps voice unchanged
            if a.dur is not None:
                n = int(round(a.dur * 48000))
                y = np.pad(y, (0, max(0, n - len(y))))[:n] if len(y) < n else y[:n]
            with wave.open(str(vd / "voice.wav"), "wb") as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(48000)
                w.writeframes((y * 32767).astype("<i2").tobytes())
    n_words = len(words)
    dur = f", {a.dur:.3f} s" if a.dur is not None else ""
    made = "words.json + lines.json (timing preview, NO voice.wav, NO words.txt)" if a.estimate else \
        f"voice.wav (48 kHz{dur}, {a.voice} x{a.speed}) + words.json + words.txt + lines.json"
    print(f"{vd}: {made}; {n_words} words. Hand-fix words.json against words.txt; picture and mix time to it.")


def _importable(mod):
    import importlib.util
    return importlib.util.find_spec(mod) is not None


if __name__ == "__main__":
    main()
