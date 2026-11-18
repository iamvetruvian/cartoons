# Laziness lint: every shot must earn its frames.
# Usage: python scripts/shot_lint.py out/<name>/shot_manifest.json [perframe.npz] [--strict]
#   shot_manifest.json: {"shots": [{"id":1,"a":0,"b":130,"entities":[...],"lead_expr":[...],
#     "layers":[...],"events":[{"frame":88,"kind":"...","word":"..."}],
#     "camera_moves":[...],"shot_size":"CU|MS|FS|WS|aerial|insert","hold":false,"low_motion_reason":"..."}]}
#   Seed entities/layers/events from briefs/shot_<id>.md — if the lint fails, fix the scene, not the manifest.
# Exit code 1 on any FAIL. Final render must not start until this passes.
import json, sys

MIN_ENTITIES = 3       # distinct animated entities per shot
MIN_LAYERS = 2         # depth layers occupied per shot (foreground/midground/background)
MIN_EVENTS = 1         # keyframed story events per shot
MIN_MOTION = 0.4       # median frame-diff per shot (short_qa.py units); held frames sit < 0.3
MAX_HELD_FRAC = 0.6    # fraction of frames with diff < 0.3 before a shot counts as a postcard
MIN_FILM_EXPR = 4      # distinct lead expressions across the film
MIN_FILM_SIZES = 3     # distinct shot sizes across the film
MIN_FILM_MOVES = 3     # distinct camera moves across the film

manifest_path = sys.argv[1] if len(sys.argv) > 1 else "out/bridge/shot_manifest.json"
npz_path = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else None
strict = "--strict" in sys.argv
if strict:
    MIN_MOTION = 0.5
    MAX_HELD_FRAC = 0.45

try:
    manifest = json.load(open(manifest_path, encoding="utf-8"))
except FileNotFoundError:
    print(f"FAIL manifest missing: {manifest_path} (seed it from briefs/shot_<id>.md)")
    sys.exit(1)
shots = manifest.get("shots", [])
fails, warns = [], []

diff = None
if npz_path:
    try:
        import numpy as np
        diff = np.load(npz_path)["diff"]
    except Exception as e:
        warns.append(f"motion data unreadable ({npz_path}: {e}); motion checks skipped")
elif strict:
    fails.append("strict mode requires perframe.npz (run short_qa.py first)")

for s in shots:
    tag = f"shot {s.get('id', '?')} f{s.get('a', '?')}-{s.get('b', '?')}"
    for key in ("entities", "lead_expr", "layers", "events", "camera_moves", "shot_size"):
        if key not in s:
            fails.append(f"{tag}: manifest missing '{key}'")
    ents = s.get("entities", [])
    if len(set(ents)) < MIN_ENTITIES:
        fails.append(f"{tag}: only {len(set(ents))} animated entities {sorted(set(ents))}, need >={MIN_ENTITIES}")
    if len(set(s.get("layers", []))) < MIN_LAYERS:
        fails.append(f"{tag}: only {len(set(s.get('layers', [])))} depth layers {s.get('layers', [])}, need >={MIN_LAYERS}")
    if len(s.get("events", [])) < MIN_EVENTS:
        fails.append(f"{tag}: no keyframed story event tied to a word, need >={MIN_EVENTS}")
    if not s.get("lead_expr"):
        fails.append(f"{tag}: lead has no expression keys")
    if diff is not None and isinstance(s.get("a"), int) and isinstance(s.get("b"), int):
        a, b = max(0, s["a"]), min(len(diff), s["b"] - 1)
        if b > a:
            import numpy as np
            seg = diff[a:b]
            med = float(np.median(seg))
            held = float((seg < 0.3).mean())
            if med < MIN_MOTION and not s.get("low_motion_reason"):
                fails.append(f"{tag}: motion median {med:.2f} < {MIN_MOTION} (postcard shot?) — restage or justify with low_motion_reason")
            if held > MAX_HELD_FRAC and not s.get("low_motion_reason"):
                fails.append(f"{tag}: held {held * 100:.0f}% of frames (diff<0.3) — every hold needs a creeping push-in")


def runs(key, label):
    seq = [s.get(key) for s in shots]
    for i in range(len(seq) - 2):
        a = seq[i]
        a0 = a[0] if isinstance(a, list) and a else a
        if not a0:
            continue
        b, c = seq[i + 1], seq[i + 2]
        b0 = b[0] if isinstance(b, list) and b else b
        c0 = c[0] if isinstance(c, list) and c else c
        if a0 == b0 == c0:
            fails.append(f"shots {shots[i]['id']}-{shots[i + 2]['id']}: same {label} '{a0}' 3 in a row — vary it")


runs("lead_expr", "lead expression")
runs("shot_size", "shot size")
runs("camera_moves", "camera move")

film_expr = {e for s in shots for e in (s.get("lead_expr") or [])}
film_sizes = {s.get("shot_size") for s in shots if s.get("shot_size")}
film_moves = {m for s in shots for m in (s.get("camera_moves") or [])}
if len(film_expr) < MIN_FILM_EXPR:
    fails.append(f"film: only {len(film_expr)} distinct lead expressions {sorted(film_expr)}, need >={MIN_FILM_EXPR} — leads are template-smiling")
if len(film_sizes) < MIN_FILM_SIZES:
    fails.append(f"film: only {len(film_sizes)} distinct shot sizes {sorted(film_sizes)}, need >={MIN_FILM_SIZES}")
if len(film_moves) < MIN_FILM_MOVES:
    fails.append(f"film: only {len(film_moves)} distinct camera moves {sorted(film_moves)}, need >={MIN_FILM_MOVES}")

for s in shots:
    ev_frames = [e.get("frame") for e in s.get("events", []) if isinstance(e.get("frame"), int)]
    for f in ev_frames:
        if not (s["a"] <= f < s["b"]):
            fails.append(f"shot {s['id']}: event at frame {f} outside shot range f{s['a']}-{s['b'] - 1}")

print(f"shot_lint: {len(shots)} shots, thresholds entities>={MIN_ENTITIES} layers>={MIN_LAYERS} events>={MIN_EVENTS} motion>={MIN_MOTION}")
for w in warns:
    print("WARN", w)
if fails:
    for f in fails:
        print("FAIL", f)
    print(f"shot_lint: {len(fails)} FAILs — fix the scenes, then re-run")
    sys.exit(1)
print("shot_lint: PASS")
