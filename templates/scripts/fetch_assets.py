# fetch_assets.py — fetch-first asset sourcing with a permanent local cache.
# Usage:
#   python scripts/fetch_assets.py list <keywords...>            # search LOCAL cache first, always
#   python scripts/fetch_assets.py search <keywords...> [--source pizza|kenney]
#   python scripts/fetch_assets.py preview pizza <model-id>
#   python scripts/fetch_assets.py preview kenney <kit>/<model>
#   python scripts/fetch_assets.py fetch pizza <model-id> [--name <slug>]
#   python scripts/fetch_assets.py fetch kenney <kit>/<model>
#   python scripts/fetch_assets.py models kenney <kit>          # list .glb names in a kit
#   python scripts/fetch_assets.py kenney-catalog                # refresh kit list
#   python scripts/fetch_assets.py gate <file.glb> [--deep]     # Gate 1 on any file
# Cache: ~/.cartoon-3d-short/assets/<source>/<id>/{model.glb,preview.jpg,meta.json,Textures/}
# Gate 1 (parseable/workable) runs on every fetch; Gate 2 (looks right) is an
# eyeball on the preview + a scene still. Licence is recorded, never a reject reason.
import sys, os, json, re, struct, time, shutil, zipfile, subprocess
import urllib.request, urllib.parse
from http.cookiejar import CookieJar

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"}
CACHE = os.path.expanduser("~/.cartoon-3d-short/assets")
HERE = os.path.dirname(os.path.abspath(__file__))
MAX_BYTES, MAX_VERTS = 100_000_000, 2_000_000  # unworkable beyond this (Gate 1 budget)

_jar = CookieJar()
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_jar))


def http(url, referer=None, timeout=40):
    req = urllib.request.Request(url, headers={**UA, **({"Referer": referer} if referer else {})})
    with _opener.open(req, timeout=timeout) as r:
        return r.read()


def save(url, path, referer=None):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = http(url, referer)
    open(path, "wb").write(data)
    return path, len(data)


def index_path():
    return os.path.join(CACHE, "index.json")


def load_index():
    try:
        return json.load(open(index_path(), encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def write_index(entries):
    os.makedirs(CACHE, exist_ok=True)
    json.dump(entries, open(index_path(), "w", encoding="utf-8"), indent=1)


def index_upsert(entry):
    entries = [e for e in load_index() if not (e["source"] == entry["source"] and e["id"] == entry["id"])]
    entries.append(entry)
    write_index(entries)


# ---------------- Gate 1: parseable and workable ----------------
def gate1(path):
    """Pure-stdlib GLB validation. Returns (ok, report-or-reason)."""
    try:
        size = os.path.getsize(path)
    except OSError:
        return False, f"unreadable file: {path}"
    if size > MAX_BYTES:
        return False, f"{size} bytes > {MAX_BYTES} budget — unworkable"
    d = open(path, "rb").read()
    if len(d) < 20:
        return False, "file too small to be a GLB"
    magic, ver, ln = struct.unpack("<III", d[:12])
    if magic != 0x46546C67:
        return False, f"bad magic {magic:#x} — not a GLB"
    if ver != 2:
        return False, f"glTF version {ver} — need v2"
    if ln != len(d):
        return False, f"length prefix {ln} != file size {len(d)} — truncated?"
    clen, ctype = struct.unpack("<II", d[12:20])
    if ctype != 0x4E4F534A:
        return False, "first chunk is not JSON"
    try:
        j = json.loads(d[20:20 + clen])
    except json.JSONDecodeError as e:
        return False, f"JSON chunk unparseable: {e}"
    meshes = j.get("meshes", [])
    if not meshes:
        return False, "zero meshes"
    prims = sum(len(m.get("primitives", [])) for m in meshes)
    if not prims:
        return False, "zero primitives"
    accessors, views = j.get("accessors", []), j.get("bufferViews", [])
    verts = sum(a.get("count", 0) for m in meshes for p in m.get("primitives", [])
                for a in [accessors[p["attributes"]["POSITION"]]] if "POSITION" in p.get("attributes", {}))
    if verts == 0:
        return False, "zero vertices"
    if verts > MAX_VERTS:
        return False, f"{verts} verts > {MAX_VERTS} budget — unworkable"
    external = sorted({img["uri"] for img in j.get("images", []) if "uri" in img})
    embedded = sum(1 for img in j.get("images", []) if "bufferView" in img)
    materials = [m.get("name", "?") for m in j.get("materials", [])]
    dims = glb_bbox(d, j)  # best-effort metres, None when accessors are exotic
    return True, {"bytes": size, "meshes": len(meshes), "prims": prims, "verts": verts,
                  "materials": materials, "external": external, "embedded_images": embedded,
                  "dims": dims, "animated": bool(j.get("animations")), "skins": bool(j.get("skins"))}


def glb_bbox(d, j):
    """Min/max over POSITION accessors (float vec3, interleaved-aware). None if exotic."""
    # BIN chunk sits right after the JSON chunk
    try:
        clen = struct.unpack("<I", d[12:16])[0]
    except Exception:
        return None
    bin_off = 20 + clen
    if bin_off + 8 > len(d):
        return None
    _, btype = struct.unpack("<II", d[bin_off:bin_off + 8])
    if btype != 0x004E4942:
        return None  # no BIN chunk (external .bin — dims unknown, still usable)
    blob = d[bin_off + 8:]
    views, accs, bufs = j.get("bufferViews", []), j.get("accessors", []), j.get("buffers", [])
    if bufs and bufs[0].get("uri"):
        return None
    lo, hi = [1e18] * 3, [-1e18] * 3
    seen = False
    for m in j.get("meshes", []):
        for p in m.get("primitives", []):
            ai = p.get("attributes", {}).get("POSITION")
            if ai is None:
                continue
            a = accs[ai]
            if a.get("componentType") != 5126 or a.get("type") != "VEC3" or "sparse" in a:
                return None
            v = views[a["bufferView"]]
            stride = v.get("byteStride", 12)
            start = v.get("byteOffset", 0) + a.get("byteOffset", 0)
            n = a["count"]
            if start + (n - 1) * stride + 12 > len(blob):
                return None
            for i in range(n):
                x, y, z = struct.unpack("<fff", blob[start + i * stride:start + i * stride + 12])
                lo[0], lo[1], lo[2] = min(lo[0], x), min(lo[1], y), min(lo[2], z)
                hi[0], hi[1], hi[2] = max(hi[0], x), max(hi[1], y), max(hi[2], z)
                seen = True
    if not seen:
        return None
    r = lambda v: round(v, 3)
    return {"min": [r(v) for v in lo], "max": [r(v) for v in hi],
            "size": [r(hi[i] - lo[i]) for i in range(3)]}


def deep_check(path):
    """Best-effort GLTFLoader.parseAsync when node+three exist. Returns (status, msg)."""
    node = shutil.which("node")
    if not node:
        return "skip", "node not installed"
    roots = [os.environ.get("FETCH_ASSETS_NODE_MODULES", ""),
             os.path.join(os.getcwd(), "node_modules"),
             os.path.expanduser("~/.cartoon-3d-short/node_modules")]
    pkg = next((os.path.join(r, "three", "package.json") for r in roots if r and os.path.exists(os.path.join(r, "three", "package.json"))), None)
    if not pkg:
        return "skip", "three not found (set FETCH_ASSETS_NODE_MODULES to a node_modules with three)"
    threedir = os.path.dirname(pkg)
    # ESM ignores NODE_PATH, so run from inside the three package (relative imports + self-reference)
    tmp = os.path.join(threedir, "deep_check_tmp.mjs")
    open(tmp, "w").write(
        "globalThis.self=globalThis;\n"
        "import { Box3 } from './build/three.module.js';\n"
        "import { GLTFLoader } from './examples/jsm/loaders/GLTFLoader.js';\n"
        "import { readFile } from 'node:fs/promises';\n"
        "const b=await readFile(process.argv[2]);\n"
        "const g=await new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');\n"
        "let m=0;g.scene.traverse(o=>{if(o.isMesh)m++;});\n"
        "console.log('meshes='+m);")
    try:
        p = subprocess.run([node, tmp, path], capture_output=True, text=True, timeout=120)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    if p.returncode != 0:
        return "fail", (p.stderr or p.stdout)[-300:]
    return "pass", p.stdout.strip()[-100:]


# ---------------- Poly Pizza ----------------
def pizza_search(query):
    url = "https://poly.pizza/search/" + urllib.parse.quote(query)
    html = http(url).decode("utf-8", "replace")
    out, seen = [], set()
    for m in re.finditer(r'href="(/m/[A-Za-z0-9_-]+)"', html):
        pid = m.group(1)[3:]
        if pid in seen:
            continue
        seen.add(pid)
        # title anchor carries direct text; the thumbnail link (same href) comes separately
        title = re.search(r"/m/" + re.escape(pid) + r"\">([^<>]{2,80})</a>", html)
        author = re.search(r'href="/u/([^"]+)"', html[m.start():m.start() + 1500])
        img = re.search(r'src="(https://static\.poly\.pizza/[^"]+\.webp)"', html[max(0, m.start() - 2000):m.start() + 800])
        out.append({"id": pid, "title": title.group(1) if title else "?",
                    "author": urllib.parse.unquote(author.group(1)) if author else "?",
                    "thumb": img.group(1) if img else None,
                    "page": "https://poly.pizza" + m.group(1)})
    return out


def pizza_model(pid):
    html = http(f"https://poly.pizza/m/{pid}").decode("utf-8", "replace")
    og = lambda p: (re.search(r'property="og:' + p + r'" content="([^"]+)"', html) or [None, None])[1]
    lic = re.search(r'"Licence":"([^"]+)"', html)
    author = re.search(r'href="/u/([^"]+)"', html)
    uuid = re.search(r"https://static\.poly\.pizza/([0-9a-f-]{36})\.glb", html)
    return {"title": og("title"), "preview": og("image"), "author": urllib.parse.unquote(author.group(1)) if author else None,
            "licence": lic.group(1) if lic else "unstated (see page)",
            "glb": f"https://static.poly.pizza/{uuid.group(1)}.glb" if uuid else None}


# ---------------- Kenney ----------------
def kenney_catalog_path():
    cached = os.path.join(CACHE, "kenney_catalog.txt")
    if os.path.exists(cached):
        return cached
    for cand in (os.path.join(HERE, "kenney_catalog.txt"), os.path.join(HERE, "..", "assets", "kenney_catalog.txt")):
        if os.path.exists(cand):
            return cand
    return None


def kenney_catalog():
    p = kenney_catalog_path()
    if not p:
        return []
    return [l.strip() for l in open(p, encoding="utf-8") if l.strip() and not l.startswith("#")]


def kenney_kit_info(slug):
    html = http(f"https://kenney.nl/assets/{slug}").decode("utf-8", "replace")
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))
    files = re.search(r"Files\s+(\d+)", text)
    tags = re.findall(r"""href=['"]https://kenney\.nl/assets/tag:([a-z0-9-]+)['"]""", html)
    sample = re.search(r'(https://kenney\.nl/media/pages/assets/%s/[^"]*?sample\.png)' % re.escape(slug), html)
    dlid = re.search(r"data-download-id='([0-9a-f]+)'", html)
    return {"slug": slug, "files": files.group(1) if files else "?", "tags": sorted(set(tags))[:8],
            "sample": sample.group(1) if sample else None, "dlid": dlid.group(1) if dlid else None}


def kenney_zip(slug):
    """Download (once, cached) the kit zip via the signed-link flow. Returns zip path."""
    zp = os.path.join(CACHE, "kenney", slug + ".zip")
    if os.path.exists(zp):
        return zp
    info = kenney_kit_info(slug)
    if not info["dlid"]:
        raise RuntimeError(f"no download id on kit page (bad slug?): {slug}")
    page = f"https://kenney.nl/assets/{slug}"
    data = json.loads(http(f"https://kenney.nl/download-link/{info['dlid']}", referer=page).decode("utf-8"))
    if "url" not in data:
        raise RuntimeError(f"signed link refused: {data} (retry; the endpoint needs cookies+Referer)")
    save(data["url"], zp, referer=page)
    return zp


def kenney_glbs(slug):
    zp = kenney_zip(slug)
    with zipfile.ZipFile(zp) as z:
        return sorted(n for n in z.namelist() if n.lower().endswith(".glb"))


# ---------------- cache writes ----------------
def cache_entry(source, cid, title, author, licence, url, glb_bytes_name, preview_url, gate, deep, extra_files=None):
    d = os.path.join(CACHE, source, cid)
    os.makedirs(d, exist_ok=True)
    meta = {"source": source, "id": cid, "title": title, "author": author, "licence": licence,
            "url": url, "fetched": time.strftime("%Y-%m-%d"), "file": "model.glb",
            "gate1": gate, "deep": deep, "extra": extra_files or []}
    if preview_url:
        try:
            save(preview_url, os.path.join(d, "preview.jpg"))
            meta["preview"] = "preview.jpg"
        except Exception as e:
            meta["preview_error"] = str(e)[-120:]
    json.dump(meta, open(os.path.join(d, "meta.json"), "w", encoding="utf-8"), indent=1)
    index_upsert({"keys": f"{title} {author} {source} {cid}".lower(), "source": source, "id": cid,
                  "path": os.path.join(d, "model.glb"), "licence": licence})
    return d, meta


# ---------------- commands ----------------
def cmd_list(keywords):
    kws = [k.lower() for k in keywords]
    hits = [e for e in load_index() if all(k in e["keys"] for k in kws)]
    if not hits:
        print(f"cache: no hit for '{' '.join(keywords)}' — search sources next")
        return
    for e in hits:
        print(f"  cached {e['source']}/{e['id']} [{e['licence']}] {e['path']}")


def cmd_search(keywords, source):
    q = " ".join(keywords)
    if source in ("all", "pizza"):
        print(f"poly.pizza /search/{q}:")
        try:
            for r in pizza_search(q)[:21]:
                print(f"  {r['id']} | {r['title']} | by {r['author']} | {r['page']}")
        except Exception as e:
            print(f"  search failed: {e}")
    if source in ("all", "kenney"):
        print(f"kenney catalog match for '{q}':")
        kws = [k.lower() for k in keywords]
        for slug in kenney_catalog():
            if all(k in slug for k in kws):
                try:
                    info = kenney_kit_info(slug)
                    print(f"  {slug} | files {info['files']} | tags {','.join(info['tags'])} | sample {info['sample'] or '-'}")
                except Exception as e:
                    print(f"  {slug} | page failed: {e}")


def cmd_preview(source, target):
    if source == "pizza":
        m = pizza_model(target)
        print(f"title: {m['title']}\nauthor: {m['author']}\nlicence: {m['licence']} (recorded, never a gate)\nglb: {m['glb']}")
        if not m["preview"]:
            print("no preview image exposed — fetch and judge in a still instead");
            return
        p, n = save(m["preview"], os.path.join(CACHE, "previews", f"pizza_{target}.jpg"))
        print(f"preview: {p} ({n} bytes) — VIEW IT, Gate 2 verdict in seconds")
    elif source == "kenney":
        slug, model = target.split("/", 1)
        zp = kenney_zip(slug)
        with zipfile.ZipFile(zp) as z:
            names = z.namelist()
            cand = next((n for n in names if n.endswith(f"Previews/{model}.png")), None) \
                or next((n for n in names if n.endswith(f"Isometric/{model}_NE.png")), None)
            if not cand:
                print(f"no per-model preview for {model} — judge in a still instead");
                return
            p = os.path.join(CACHE, "previews", f"kenney_{slug}_{model}.png")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            open(p, "wb").write(z.read(cand))
            print(f"preview: {p} — VIEW IT, Gate 2 verdict in seconds")
    else:
        print("preview needs pizza|kenney")


def cmd_fetch(source, target, name, deep):
    if source == "pizza":
        m = pizza_model(target)
        if not m["glb"]:
            print("REJECT: no GLB exposed on the model page");
            sys.exit(1)
        cid = name or target
        d = os.path.join(CACHE, source, cid)
        os.makedirs(d, exist_ok=True)
        gp = os.path.join(d, "model.glb")
        save(m["glb"], gp, referer=f"https://poly.pizza/m/{target}")
        ok, rep = gate1(gp)
        if not ok:
            print(f"REJECT (Gate 1): {rep}");
            sys.exit(1)
        if rep["external"]:
            print(f"REJECT (Gate 1): external refs {rep['external']} unresolvable for single-file pizza models");
            sys.exit(1)
        deep_rep = deep_check(gp) if deep else ("skip", "no --deep flag")
        dd, meta = cache_entry(source, cid, m["title"], m["author"], m["licence"],
                               f"https://poly.pizza/m/{target}", "model.glb", m["preview"], rep, deep_rep)
        print(f"PASS Gate 1: {rep['meshes']} meshes, {rep['prims']} prims, {rep['verts']} verts, dims {rep['dims']}, deep {deep_rep[0]}")
        print(f"cached: {dd}/model.glb — Gate 2: view the preview, then a scene still")
    elif source == "kenney":
        slug, model = target.split("/", 1)
        zp = kenney_zip(slug)
        with zipfile.ZipFile(zp) as z:
            names = z.namelist()
            hit = next((n for n in names if n.lower().endswith(f"/{model.lower()}.glb")), None)
            if not hit:
                print(f"REJECT: {model}.glb not in {slug} (run: models kenney {slug})");
                sys.exit(1)
            cid = name or f"{slug}__{model}"
            d = os.path.join(CACHE, source, cid)
            os.makedirs(d, exist_ok=True)
            gp = os.path.join(d, "model.glb")
            open(gp, "wb").write(z.read(hit))
            ok, rep = gate1(gp)
            if not ok:
                print(f"REJECT (Gate 1): {rep}");
                sys.exit(1)
            extras = []
            for uri in rep["external"]:
                base = os.path.basename(uri)
                sib = next((n for n in names if n.endswith(base)), None)
                if not sib:
                    print(f"REJECT (Gate 1): external ref {uri} not in kit zip");
                    sys.exit(1)
                dest = os.path.join(d, uri)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(z.read(sib))
                extras.append(uri)
            deep_rep = deep_check(gp) if deep else ("skip", "no --deep flag")
            lic = "CC0 (License.txt in kit)" if any(n.endswith("License.txt") for n in names) else "see kit page"
            dd, meta = cache_entry(source, cid, f"{model} ({slug})", "Kenney", lic,
                                   f"https://kenney.nl/assets/{slug}", "model.glb", None, rep, deep_rep, extras)
            print(f"PASS Gate 1: {rep['meshes']} meshes, {rep['prims']} prims, {rep['verts']} verts, dims {rep['dims']}, extras {extras}, deep {deep_rep[0]}")
            print(f"cached: {dd}/model.glb — Gate 2: view the preview (preview kenney {slug}/{model}), then a scene still")
    else:
        print("fetch needs pizza|kenney");
        sys.exit(1)


def cmd_models(source, slug):
    if source != "kenney":
        print("models lists kit contents — kenney only (pizza is single-model pages)");
        return
    for n in kenney_glbs(slug):
        print(" ", n)


def cmd_catalog():
    out = [f"# Kenney kit slugs (refreshed {time.strftime('%Y-%m-%d')})."]
    seen, page = set(), 1
    while page <= 40:
        html = http(f"https://kenney.nl/assets/page:{page}").decode("utf-8", "replace")
        slugs = sorted(set(re.findall(r"assets/([a-z0-9-]+)", html)) - {"category", "page", "series", "tag"})
        new = [s for s in slugs if s not in seen]
        if not new:
            break
        seen.update(new)
        page += 1
        time.sleep(0.3)
    out += sorted(seen)
    p = os.path.join(CACHE, "kenney_catalog.txt")
    os.makedirs(CACHE, exist_ok=True)
    open(p, "w", encoding="utf-8").write("\n".join(out) + "\n")
    print(f"catalog: {len(seen)} kits -> {p}")


def main(argv):
    if len(argv) < 2 or argv[1] in ("-h", "--help", "help"):
        print(__doc__.splitlines()[0]);
        print("commands: list|search|preview|fetch|models|kenney-catalog|gate  (see header for usage)");
        return
    cmd = argv[1]
    if cmd == "list":
        cmd_list(argv[2:])
    elif cmd == "search":
        args = [a for a in argv[2:] if a != "--deep"]
        source = "all"
        if "--source" in args:
            i = args.index("--source");
            source, args = args[i + 1], args[:i]
        cmd_search(args, source)
    elif cmd == "preview" and len(argv) >= 4:
        cmd_preview(argv[2], argv[3])
    elif cmd == "fetch" and len(argv) >= 4:
        args = argv[4:]
        name = args[args.index("--name") + 1] if "--name" in args else None
        cmd_fetch(argv[2], argv[3], name, "--deep" in args)
    elif cmd == "models" and len(argv) >= 4:
        cmd_models(argv[2], argv[3])
    elif cmd == "kenney-catalog":
        cmd_catalog()
    elif cmd == "gate" and len(argv) >= 3:
        ok, rep = gate1(argv[2])
        if not ok:
            print(f"REJECT (Gate 1): {rep}");
            sys.exit(1)
        deep_rep = deep_check(argv[2]) if "--deep" in argv else ("skip", "no --deep flag")
        print(f"PASS Gate 1: {rep['meshes']} meshes, {rep['prims']} prims, {rep['verts']} verts, dims {rep['dims']}, deep {deep_rep}")
    else:
        print("unknown command — see header for usage");
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv)
