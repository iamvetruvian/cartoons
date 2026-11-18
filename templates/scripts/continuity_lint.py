# Causality lint: nothing is visible before its cause, nobody teleports, places never merge.
# Usage: python scripts/continuity_lint.py out/<name>/continuity.json
#   continuity.json: {"sets": {id: {"int_ext": "INT|EXT"}},
#     "entities": {name: {"kind": "lead|crowd|prop", "home": set|null, "travels": bool,
#                          "intro_shot": int, "intro_why": str}},
#     "shots": [{"id":1, "set": set,
#       "entities": [{"name": str, "presence": "entered|resident|cut-in", "via": str?, "frame": int?}],
#       "knows": [...], "teaches": [...], "depicts": [...], "nouns": [...],
#       "metaphor": {"tenor": str, "vehicle": str, "staged": "sequence"}?}]}
# Seed it from briefs/shot_<id>.md (presence/knows/teaches/depicts/nouns/metaphor slots).
# depicts/nouns share one lowercase concept vocabulary (singular keys: emu, not "emus"/"birds").
# Exit code 1 on any FAIL. Final render must not start until this passes.
import json
import sys

MAX_COVERAGE = 0.8   # |depicts ∩ nouns| / |nouns| above this = the shot depicts everything (literalism)
MIN_NOUNS = 4        # sentences under this many concepts are exempt: a 3-concept situation shot
# (gun + targets + place) that depicts all three is correct staging, not literalism. Cramming
# (4/4, 5/5+) is what fails. Metaphor composites and pre-placed agents are caught by the
# metaphor/home/intro rules instead — each rule has its own prey.

manifest_path = sys.argv[1] if len(sys.argv) > 1 else "out/bridge/continuity.json"
try:
    manifest = json.load(open(manifest_path, encoding="utf-8"))
except FileNotFoundError:
    print(f"FAIL manifest missing: {manifest_path} (seed it from briefs/shot_<id>.md)")
    sys.exit(1)

sets = manifest.get("sets", {})
entities = manifest.get("entities", {})
shots = sorted(manifest.get("shots", []), key=lambda s: s.get("id", 0))
fails, warns = [], []
norm = lambda s: str(s).strip().lower()


def tag(shot_id, name=None):
    return f"shot {shot_id}" + (f" '{name}'" if name else "")


for sid, s in sets.items():
    if s.get("int_ext") not in ("INT", "EXT"):
        fails.append(f"set '{sid}': int_ext must be INT|EXT")

for name, e in entities.items():
    t = f"entity '{name}'"
    if e.get("kind") not in ("lead", "crowd", "prop"):
        fails.append(f"{t}: kind must be lead|crowd|prop")
    home = e.get("home")
    if home is None:
        if not e.get("travels"):
            fails.append(f"{t}: home is null without travels=true — everything lives somewhere; name its home set")
    elif home not in sets:
        fails.append(f"{t}: home '{home}' is not a declared set — declare the place or fix the home")
    if not isinstance(e.get("intro_shot"), int):
        fails.append(f"{t}: intro_shot must be an int (the shot the story motivates it)")
    if not (e.get("intro_why") or "").strip():
        fails.append(f"{t}: intro_why is empty — state the story beat that motivates it")

appearances = {}  # name -> [(shot_id, set, entry)]
for s in shots:
    sid = s.get("id", "?")
    if s.get("set") not in sets:
        fails.append(f"shot {sid}: set '{s.get('set')}' is not a declared set")
    for key in ("entities", "knows", "teaches", "depicts", "nouns"):
        if key not in s:
            fails.append(f"shot {sid}: manifest missing '{key}'")
    for e in s.get("entities", []):
        name = e.get("name")
        if name not in entities:
            fails.append(f"shot {sid}: entity '{name}' is not declared in entities")
            continue
        appearances.setdefault(name, []).append((sid, s.get("set"), e))
    m = s.get("metaphor")
    if m is not None:
        if m.get("staged") != "sequence":
            fails.append(f"shot {sid}: metaphor '{m.get('tenor', '?')}'/'{m.get('vehicle', '?')}' "
                         f"staged as '{m.get('staged', '?')}' — tenor and vehicle are always a CUT SEQUENCE, "
                         f"never a composite (split the setup and cut)")
        for key in ("tenor", "vehicle"):
            if not (m.get(key) or "").strip():
                fails.append(f"shot {sid}: metaphor missing '{key}'")
    nouns = [norm(n) for n in s.get("nouns", [])]
    if not nouns:
        fails.append(f"shot {sid}: nouns[] is empty — declare the sentence's concept keys")
    else:
        depicts = {norm(d) for d in s.get("depicts", [])}
        if len(nouns) >= MIN_NOUNS:
            cov = len(depicts & set(nouns)) / len(nouns)
            if cov > MAX_COVERAGE:
                fails.append(f"shot {sid}: noun coverage {cov:.2f} > {MAX_COVERAGE} "
                             f"(depicts {sorted(depicts & set(nouns))} of {nouns}) — restage to the meaning, not the words")

for name, apps in appearances.items():
    e = entities[name]
    first = min(a[0] for a in apps)
    if first < e.get("intro_shot", 0):
        fails.append(f"{tag(first, name)}: visible before its cause (intro_shot {e.get('intro_shot')}: "
                     f"{e.get('intro_why', '')}) — enter it on screen or cut to it, no earlier")
    for i, (sid, sset, ent) in enumerate(apps):
        p = ent.get("presence")
        if p not in ("entered", "resident", "cut-in"):
            fails.append(f"{tag(sid, name)}: presence must be entered|resident|cut-in (there is no "
                         f"'pre-placed for the camera' — stage an entrance or a cut)")
            continue
        if p == "entered" and (not (ent.get("via") or "").strip() or not isinstance(ent.get("frame"), int)):
            fails.append(f"{tag(sid, name)}: entered requires via (from where/how) + frame")
        if p == "resident":
            if e.get("travels"):
                fails.append(f"{tag(sid, name)}: travellers are never resident — tag entered with via")
            elif e.get("home") != sset:
                fails.append(f"{tag(sid, name)}: resident of '{e.get('home')}' staged in '{sset}' — "
                             f"residents stay home; move the setup or enter them properly")
        if p == "cut-in" and sid != first:
            fails.append(f"{tag(sid, name)}: cut-in is first-appearance-only — later arrivals are "
                         f"entered with via, even via a cut")
        if i > 0 and apps[i - 1][1] != sset and p != "entered":
            fails.append(f"{tag(sid, name)}: teleported {apps[i - 1][1]} -> {sset} (was there in shot "
                         f"{apps[i - 1][0]}) without travel — tag entered with via, or stage the journey")

for s in shots:
    residents = [e["name"] for e in s.get("entities", [])
                 if e.get("presence") == "resident" and e.get("name") in entities]
    homes = {entities[n].get("home") for n in residents} - {None}
    if len(homes) >= 2:
        fails.append(f"shot {s.get('id')}: merged places — residents of {sorted(homes)} share one setup "
                     f"({residents}) — split the setup and cut; per-shot visibility never smuggles a second place in")

by_id = {s.get("id"): s for s in shots}
ids = sorted(by_id)
for a, b in zip(ids, ids[1:]):
    taught = {norm(t) for t in by_id[a].get("teaches", [])}
    known = {norm(t) for t in by_id[b].get("knows", [])}
    dropped = taught - known
    if dropped:
        fails.append(f"shots {a}->{b}: teaches {sorted(dropped)} never reaches shot {b}'s knows — "
                     f"audience knowledge is cumulative; maintain the chain")
for name, apps in appearances.items():
    first = min(a[0] for a in apps)
    taught = {norm(t) for t in by_id[first].get("teaches", [])}
    if norm(name) not in taught:
        fails.append(f"{tag(first, name)}: first appearance not named in teaches[] — "
                     f"introductions go on the record")

print(f"continuity_lint: {len(shots)} shots, {len(entities)} entities, coverage<={MAX_COVERAGE}")
for w in warns:
    print("WARN", w)
if fails:
    for f in fails:
        print("FAIL", f)
    print(f"continuity_lint: {len(fails)} FAILs — restage (cut, entrance, sequence), never weaken the ledger")
    sys.exit(1)
print("continuity_lint: PASS")
