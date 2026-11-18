# perf_budget.py — the canvas pool must fit in memory: gate the high-water marks.
# Usage: python scripts/perf_budget.py <stills.log|perf.json> [--strict]
#   Collect samples first: flip PERF_DUMP in world.ts (or DUMP_PERF=1), render
#   stills across every shot (bridge-stills.mjs prints PERF_JSON lines), and run
#   this on the log. It takes the per-shot maxima of live canvases and bytes.
# Thresholds (defaults generous; calibrate down per project): live <= 64
# canvases/shot, bytes <= 512 MB/shot. --strict: 32 canvases, 256 MB.
# Face-count caps (<=12 lead / <=8 crowd distinct faces per shot) stay verified
# via the expression sheets (CHARACTER_DESIGN.md), not here. Exit 1 on any FAIL.
import json, sys

path = sys.argv[1] if len(sys.argv) > 1 else "out/bridge/stills.log"
strict = "--strict" in sys.argv
MAX_LIVE, MAX_MB = (32, 256) if strict else (64, 512)

raw = open(path, encoding="utf-8").read()
samples = []
if path.endswith(".json"):
    try:
        doc = json.loads(raw)
        samples = doc if isinstance(doc, list) else doc.get("samples", [])
    except json.JSONDecodeError:
        pass
if not samples:
    for line in raw.splitlines():
        i = line.find("PERF_JSON ")
        if i >= 0:
            try:
                samples.append(json.loads(line[i + 10:]))
            except json.JSONDecodeError:
                pass
if not samples:
    print(f"FAIL no PERF_JSON samples in {path} — flip PERF_DUMP and render stills first")
    sys.exit(1)

shots = {}
for s in samples:
    sid = s.get("id", "?")
    cur = shots.setdefault(sid, {"live": 0, "mb": 0.0, "n": 0})
    cur["live"] = max(cur["live"], s.get("live", 0))
    cur["mb"] = max(cur["mb"], s.get("bytes", 0) / 1e6)
    cur["n"] += 1

fails = []
for sid in sorted(shots):
    c = shots[sid]
    print(f"  shot {sid}: max live {c['live']} canvases, {c['mb']:.0f} MB ({c['n']} samples)")
    if c["live"] > MAX_LIVE:
        fails.append(f"shot {sid}: {c['live']} live canvases > {MAX_LIVE} — coarsen face quantization (ACTING.md) before simplifying acting")
    if c["mb"] > MAX_MB:
        fails.append(f"shot {sid}: {c['mb']:.0f} MB > {MAX_MB} MB — shrink canvas tiers or crowd variety")

print(f"perf_budget: {len(shots)} shots, caps {MAX_LIVE} live / {MAX_MB} MB")
if fails:
    for f in fails:
        print("FAIL", f)
    sys.exit(1)
print("perf_budget: PASS")
