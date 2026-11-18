# material_check.py — no accidental palette: every GLB material is recoloured or allowed.
# Usage: python scripts/material_check.py <project-root> <video>
#   video = src/videos/<video>/build.ts + public/<video>/**/*.glb
# Parses each shipped GLB's material names (via fetch_assets Gate 1) and requires
# each to be in build.ts RECOLOR, the leafsGreen special, or MATERIAL_ALLOW.
# Anything else falls back to source colors — sometimes intended (flower petals),
# usually a teal/purple surprise — so it FAILS until the agent maps it in RECOLOR
# or deliberately adds it to MATERIAL_ALLOW with a comment. Exit 1 on any FAIL.
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fetch_assets import gate1

root, video = sys.argv[1], sys.argv[2]
build_path = os.path.join(root, "src", "videos", video, "build.ts")
pub = os.path.join(root, "public", video)
fails = []

try:
    build = open(build_path, encoding="utf-8").read()
except FileNotFoundError:
    print(f"FAIL missing {build_path}")
    sys.exit(1)
mapped = set()
m = re.search(r"RECOLOR[^=]*=\s*\{(.*?)\};", build, re.S)
if m:
    mapped |= set(re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\s*:", m.group(1)))
m = re.search(r"MATERIAL_ALLOW\s*=\s*\[(.*?)\]", build, re.S)
if m:
    mapped |= set(re.findall(r'"([^"]+)"', m.group(1)))
else:
    fails.append("build.ts has no MATERIAL_ALLOW — add it (deliberate source-color names, with a comment)")
mapped.add("leafsGreen")  # GREENS special in toLambert
if "toLambert" not in build:
    fails.append("build.ts has no toLambert — kit materials bypass the house lighting model")

glbs = []
for dirpath, _, files in os.walk(pub):
    glbs += [os.path.join(dirpath, f) for f in files if f.endswith(".glb")]
if not glbs:
    fails.append(f"no .glb files under {pub}")
checked = set()
for p in sorted(glbs):
    ok, rep = gate1(p)
    if not ok:
        fails.append(f"{os.path.basename(p)}: unparseable ({rep})")
        continue
    for mat in rep["materials"]:
        checked.add(mat)
        if mat not in mapped:
            fails.append(f"{os.path.basename(p)}: material '{mat}' unmapped — add to RECOLOR or MATERIAL_ALLOW")

print(f"material_check: {video}: {len(glbs)} GLBs, {len(checked)} materials ({len(mapped)} mapped)")
if fails:
    for f in fails:
        print("FAIL", f)
    sys.exit(1)
print("material_check: PASS")
