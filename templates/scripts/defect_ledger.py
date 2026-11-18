# Defect ledger: every visual bug is tracked, fixed granularly, and proven fixed.
# Usage:
#   python scripts/defect_ledger.py out/<name>/defects.json init
#   python scripts/defect_ledger.py out/<name>/defects.json add --shot 6 --frame 720 --class floating --desc "lead floats 5cm" --before out/<name>/fix/720_before.jpg
#   python scripts/defect_ledger.py out/<name>/defects.json round --id 1        # log one VLM critique round (cap 3)
#   python scripts/defect_ledger.py out/<name>/defects.json fix --id 1 --after out/<name>/fix/720_after.jpg
#   python scripts/defect_ledger.py out/<name>/defects.json verify --id 1       # after re-checking the after-crop
#   python scripts/defect_ledger.py out/<name>/defects.json gate               # PASS only when all verified
# Rules: done is illegal with open items; every fix needs a before AND after crop
# at the SAME frame; render per shot so a fix costs seconds; VLM critique is
# capped at 3 rounds per defect — programmatic checks come first.
# Class `sense` is for spatial/causal nonsense: unmotivated presence, teleports,
# composite metaphors, pans to pre-placed elements. Log it the turn you see it.
import json, os, sys

CLASSES = {"floating", "passthrough", "occlusion", "caption", "face", "fx", "audio", "camera", "sense", "other"}
MAX_ROUNDS = 3

path, cmd = sys.argv[1], sys.argv[2]
args = sys.argv[3:]
opt = {args[i][2:]: args[i + 1] for i in range(0, len(args), 2) if args[i].startswith("--")}


def load():
    if not os.path.exists(path):
        return {"defects": []}
    return json.load(open(path, encoding="utf-8"))


def save(db):
    json.dump(db, open(path, "w", encoding="utf-8"), indent=1)
    print(f"ledger: {path} ({len(db['defects'])} defects)")


if cmd == "init":
    if os.path.exists(path):
        print(f"ledger exists: {path}")
    else:
        save({"defects": []})
elif cmd == "add":
    cls = opt.get("class", "other")
    if cls not in CLASSES:
        print(f"unknown class '{cls}', use one of {sorted(CLASSES)}")
        sys.exit(1)
    db = load()
    did = max([d["id"] for d in db["defects"]], default=0) + 1
    db["defects"].append({"id": did, "shot": int(opt["shot"]), "frame": int(opt["frame"]),
                          "class": cls, "desc": opt.get("desc", ""), "status": "open",
                          "before": opt.get("before"), "after": None, "rounds": 0})
    save(db)
    print(f"added #{did} [{cls}] shot {opt['shot']} f{opt['frame']}: {opt.get('desc', '')}")
elif cmd in ("round", "fix", "verify"):
    db = load()
    ds = [d for d in db["defects"] if d["id"] == int(opt["id"])]
    if not ds:
        print(f"no defect #{opt['id']}")
        sys.exit(1)
    d = ds[0]
    if cmd == "round":
        d["rounds"] += 1
        print(f"#{d['id']}: round {d['rounds']}/{MAX_ROUNDS}")
    elif cmd == "fix":
        d["after"] = opt.get("after")
        d["status"] = "fixed"
        print(f"#{d['id']}: fixed -> {d['after']} (verify the after-crop, then run verify)")
    else:
        if d["status"] != "fixed":
            print(f"#{d['id']}: status is {d['status']}, run fix first")
            sys.exit(1)
        d["status"] = "verified"
        print(f"#{d['id']}: verified")
    save(db)
elif cmd == "gate":
    db = load()
    fails = []
    for d in db["defects"]:
        tag = f"#{d['id']} [{d['class']}] shot {d['shot']} f{d['frame']}"
        if d["status"] == "open":
            fails.append(f"{tag}: OPEN — {d['desc']}")
        elif d["status"] == "fixed":
            fails.append(f"{tag}: fixed but UNVERIFIED — re-check the after-crop and run verify")
        else:
            for side in ("before", "after"):
                if not d.get(side) or not os.path.exists(d[side]):
                    fails.append(f"{tag}: verified without a '{side}' crop at the same frame ({d.get(side)})")
        if d.get("rounds", 0) > MAX_ROUNDS:
            fails.append(f"{tag}: {d['rounds']} VLM rounds > cap {MAX_ROUNDS} — resolve programmatically, do not loop the verifier")
    if fails:
        print(f"ledger gate: {len(fails)} FAILs")
        for f in fails:
            print("FAIL", f)
        sys.exit(1)
    print(f"ledger gate: PASS ({len(db['defects'])} defects, all verified with before/after crops)")
elif cmd == "list":
    db = load()
    for d in db["defects"]:
        print(f"#{d['id']} [{d['status']}] {d['class']} shot {d['shot']} f{d['frame']} r{d.get('rounds', 0)}: {d['desc']}")
else:
    print("commands: init|add|round|fix|verify|gate|list")
    sys.exit(1)
