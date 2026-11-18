# kit_check.py — every model the code loads must exist on disk.
# Usage: python scripts/kit_check.py <project-root> <video>
#   video = src/videos/<video>/ + public/<video>/
# Collects requested names from world.ts (KENNEY load list), story.ts
# (FOREGROUND kit:) and build.ts (prop()/kitClone() literals, pick([...]) pools),
# then verifies public/<video>/**/<name>.glb exists for each. VEG-mapped and
# banner-via-prop names are GLB-exempt (drawn procedurally); KENNEY entries that
# are never rendered from GLB are reported as dead loads. Dynamic names passed
# through variables must appear in KENNEY (the load manifest) — anything subtler
# is caught at runtime by loadKit/prop loud warnings instead. Exit 1 on missing.
import os, re, sys

root, video = sys.argv[1], sys.argv[2]
src = os.path.join(root, "src", "videos", video)
pub = os.path.join(root, "public", video)
fails, warns = [], []


def read(name):
    p = os.path.join(src, name)
    if not os.path.exists(p):
        fails.append(f"missing source file: {p}")
        return ""
    return open(p, encoding="utf-8").read()


world, story, build = read("world.ts"), read("story.ts"), read("build.ts")

kenney = []
m = re.search(r"KENNEY\s*=\s*\[(.*?)\]", world, re.S)
if m:
    kenney = re.findall(r'"([^"]+)"', m.group(1))
else:
    fails.append("world.ts: KENNEY list not found")

veg = set()
m = re.search(r"\bVEG\b[^=]*=\s*\{(.*?)\};", build, re.S)
if m:
    body = m.group(1)
    # keys only (quoted "tree-high-round" or bare tree_oak); values never precede a colon
    veg = set(re.findall(r'"([^"]+)"\s*:', body)) | set(re.findall(r"\b([A-Za-z][A-Za-z0-9_]*)\s*:", body))

prop_lit = set(re.findall(r"\bprop\(\s*[^,]+,\s*[^,]+,\s*\"([^\"]+)\"", build))
clone_lit = set(re.findall(r"\bkitClone\(\s*[^,]+,\s*\"([^\"]+)\"", build)) | set(re.findall(r"\bkitClone\(\s*[^,]+,\s*\"([^\"]+)\"", world))
pools = set()
for arr in re.findall(r"\bpick\(\[([^\]]+)\]", build):
    pools |= set(re.findall(r'"([^"]+)"', arr))
foreground = set(re.findall(r"\bkit:\s*\"([^\"]+)\"", story))

have = set()
for dirpath, _, files in os.walk(pub):
    have |= {f[:-4] for f in files if f.endswith(".glb")}
if not os.path.isdir(pub):
    fails.append(f"missing public dir: {pub}")

# who needs a GLB: KENNEY entries (minus VEG dead loads), prop names (minus
# VEG/banner procedural), kitClone names (minus VEG), FOREGROUND kits (minus VEG)
dead = sorted(set(kenney) & veg)
need = (set(kenney) - veg) | (prop_lit - veg - {n for n in prop_lit if n.startswith("banner")}) \
    | (clone_lit - veg) | (pools - veg - {n for n in pools if n.startswith("banner")}) | (foreground - veg)
for n in sorted(need):
    if n not in have:
        fails.append(f"missing public/{video}/**/{n}.glb (requested by code, renders as NOTHING today)")
for n in dead:
    warns.append(f"dead load: KENNEY lists '{n}' but VEG draws it procedurally — prune it")
for n in sorted((prop_lit | clone_lit | foreground) - set(kenney) - veg):
    if not n.startswith("banner"):
        warns.append(f"'{n}' used by code but not in KENNEY — add it or fix the typo")

print(f"kit_check: {video}: {len(kenney)} KENNEY entries, {len(have)} GLBs on disk, {len(need)} names need files")
for w in warns:
    print("WARN", w)
if fails:
    for f in fails:
        print("FAIL", f)
    print(f"kit_check: {len(fails)} FAILs — fetch the models (ASSETS.md) or fix the names")
    sys.exit(1)
print("kit_check: PASS")
