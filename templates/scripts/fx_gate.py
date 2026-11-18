# fx_gate.py — every effect earns its frame: tied to a word, short-lived, proven on stills.
# Usage: python scripts/fx_gate.py out/<name>/fx_manifest.json [--strict]
#   fx_manifest.json: {"words": "path/to/words.json", "fps": 30,
#     "fx": [{"shot": 8, "frame": 1039, "kind": "burst", "word": "snap", "dur": 14,
#             "stills": ["out/<name>/fx/snap_1037.jpg", "...1039...", "...1042..."]}]}
# Checks per fx: word exists in words.json; frame within [-3, +6] of the word onset
# (reactions anticipate, impacts land on/just after the event); dur <= 30 f (a
# continuous twinkle reads as random junk — retrigger instead); >=3 bracketed
# still paths that EXIST on disk (a lone still proves nothing either way).
# Exit code 1 on any FAIL. --strict shrinks the window to [-3, +3] and dur to <=20.
import json, os, sys

manifest_path = sys.argv[1] if len(sys.argv) > 1 else "out/bridge/fx_manifest.json"
strict = "--strict" in sys.argv
LO, HI, MAXDUR = (-3, 3, 20) if strict else (-3, 6, 30)

try:
    manifest = json.load(open(manifest_path, encoding="utf-8"))
except FileNotFoundError:
    print(f"FAIL manifest missing: {manifest_path}")
    sys.exit(1)
fps = manifest.get("fps", 30)
try:
    words = json.load(open(manifest["words"], encoding="utf-8"))
except (KeyError, FileNotFoundError) as e:
    print(f"FAIL words.json unreadable ({e}) — fx timing needs the narration timings")
    sys.exit(1)
onsets = {}
for w in words:
    k = (w.get("w") or "").strip().lower()
    if k and k not in onsets:
        onsets[k] = round(float(w["s"]) * fps)

fails = []
for e in manifest.get("fx", []):
    tag = f"shot {e.get('shot', '?')} f{e.get('frame', '?')} {e.get('kind', '?')}"
    if "word" not in e or "frame" not in e:
        fails.append(f"{tag}: needs 'word' + 'frame' (untied fx renders as random junk)")
        continue
    onset = onsets.get(str(e["word"]).strip().lower())
    if onset is None:
        fails.append(f"{tag}: word '{e['word']}' not in words.json — tie it to a real word/beat")
    elif not (LO <= e["frame"] - onset <= HI):
        fails.append(f"{tag}: frame {e['frame']} vs '{e['word']}' onset f{onset} (Δ{e['frame'] - onset:+d}) outside [{LO},+{HI}]")
    if e.get("dur", 0) > MAXDUR:
        fails.append(f"{tag}: dur {e['dur']}f > {MAXDUR}f — continuous fx reads as junk; retrigger per beat")
    stills = e.get("stills", [])
    if len(stills) < 3:
        fails.append(f"{tag}: {len(stills)} bracket stills, need >=3 across its life")
    else:
        for s in stills:
            if not os.path.exists(s):
                fails.append(f"{tag}: bracket still missing on disk: {s}")

print(f"fx_gate: {len(manifest.get('fx', []))} fx, window [{LO},+{HI}]f, dur<={MAXDUR}f")
if fails:
    for f in fails:
        print("FAIL", f)
    sys.exit(1)
print("fx_gate: PASS")
