# ASSETS.md — fetch first, create last

Load this file whenever a scene needs a prop, set piece, or background object.
Flow: need → local cache → fetch → 2-gate check → cache → place. Procedural
modeling (`build.ts`, VEG-style) is the fallback when fetching fails, not the
default. Fetching beats modeling for quality-per-effort because `build.ts`
style-normalizes everything through `toLambert` + the recolor table.

## Where needs come from

Prop needs come from the Scene Briefs (`STAGING.md`): every foreground,
midground, and background slot that names an object becomes one line on the
prop list (`props/<video>.md`: shot → object → set → status). Rules:

- If no brief names it, it doesn't get fetched. This is "every visible prop
  must earn its frame" applied at sourcing time.
- One line per distinct object, not per shot. Reuse across shots is the point.
- Mark each line `cached` (in the local library), `fetch:<source>:<id>`, or
  `create` (procedural, with a one-line reason fetching failed).

## The local cache (search here FIRST)

`~/.cartoon-3d-short/assets/` is the permanent library across all videos:

```
assets/<source>/<id>/model.glb      # the model (never edit in place)
assets/<source>/<id>/preview.jpg    # source preview for eyeball search
assets/<source>/<id>/meta.json      # source, author, licence, url, date, dims
assets/<source>/<id>/Textures/      # external siblings, when the GLB needs them
assets/index.json                   # keyword index over everything cached
```

Every download lands here via `fetch_assets.py`, which validates Gate 1 and
writes `meta.json` + the index entry. Projects copy (not move) from the cache
into `public/<video>/kenney/` or `public/<video>/pizza/`. Re-downloading a
cached model is a failure — `fetch_assets.py list <keywords>` first, always.

## The two gates (the ONLY reject reasons)

License is recorded in `meta.json` and NEVER a reject reason.

**Gate 1 — parseable and workable (machine check, `fetch_assets.py fetch`).**
The GLB must: carry valid `glTF` magic + version 2; parse its JSON chunk;
contain ≥1 mesh with ≥1 primitive and >0 vertices; resolve every external
reference (textures/images with `uri`) — siblings are fetched alongside, and
an unresolvable reference is a REJECT (the model can't be used as intended);
load inside a time/memory budget (a model that chokes the loader is
unworkable, whatever its beauty). `--deep` additionally runs
`GLTFLoader.parseAsync` when node+three are available. Scale is NOT a gate:
`prop()`/`kitClone()` normalize every model to its target height.

**Gate 2 — looks right and relevant (eyeball, cheapest first).** View the
source preview (Kenney `Previews/*.png` / `Isometric/*_NE.png`, Poly Pizza
`og:image` JPG) and decide in seconds — wrong object, wrong style
(photoreal/PBR-heavy vs flat low-poly), or an unreadable silhouette at its
target size/distance is a REJECT, and the rejection costs a thumbnail, not a
render. Final proof is the prop in a previs/scene still. One style escape
hatch: faceted geometry that fights the ink pass in close-up range goes
procedural instead (the VEG precedent) — that is a redirect, not a failure.

## Missing-model behavior (loud, never silent)

`loadKit` logs one `console.error` per missing file (surfaced by bridge-stills)
and records it in `KIT_MISSING`; `prop()`/`kitClone()` do the same once per
name (`propMissing()`). Before any render, run
`python scripts/kit_check.py <project> <video>` — it fails on every model the
code requests but `public/<video>/` lacks, and warns on dead KENNEY loads and
names used but never listed. A missing model is either a typo (fix the name)
or an unfetched asset (fetch it); there is no third case where silence is
correct.

## Source guide: Kenney (kenney.nl) — curated kits, CC0

~190 kits, each a zip of models in FBX/OBJ/GLB/DAE + per-model previews +
`License.txt` (CC0). Model names use `under_scores` (Nature Kit) or
`dash-names` (Fantasy Town Kit).

- **Find a kit:** keyword-match `templates/assets/kenney_catalog.txt`
  (refresh with `fetch_assets.py kenney-catalog`), or crawl
  `https://kenney.nl/assets/page:N`. Fetch the kit page for tags, category,
  and model count, and view its `sample.png` contact sheet (~130 KB) — every
  model at a glance, no zip needed.
- **Download (scripted, do not hand-roll):** browser `User-Agent` is mandatory
  (curl's default gets 403). Page → `data-download-id` → `GET
  /download-link/<id>` with cookies + `Referer` (else `{"error":"forbidden"}`)
  → signed zip URL (expires). `fetch_assets.py` does all of this.
- **Extract:** list the zip for `*.glb` — the folder is `Models/GLB format/`
  in some kits, `Models/GLTF format/` in others. Copy chosen models only.
- **Textures:** Nature-style kits are self-contained (plain-color materials).
  Colormap kits (Fantasy Town) reference `Textures/colormap.png` — copy the
  `Textures/` folder next to the GLBs or every prop renders white.
- **Known map (verified):** Nature Kit → 15 skill models (trees, bushes,
  flowers, grass, lily, canoe); Fantasy Town Kit → 11 (tree, tree-high-round,
  hedge, lantern, cart, 3 stalls, 2 banners, windmill).

## Source guide: Poly Pizza (poly.pizza) — 10,700+ single models, mixed licences

One model per page, direct static downloads, no account, no signed links.
Licence varies by author (CC0, CC-BY 3.0/4.0 seen) — recorded, never gated.

- **Search:** `https://poly.pizza/search/<keywords>` is server-rendered and
  returns ~21 `/m/<id>` model links per page. Filter by eye on titles first.
- **Shortlist:** fetch `/m/<id>` (static HTML embeds everything): `og:title`
  (name + author), `og:image` (preview JPG — view it, decide in seconds),
  the direct GLB at `https://static.poly.pizza/<uuid>.glb` (also in the
  modelviewer `twitter:player` URL), and a JSON blob with `"Licence"`,
  `"Type"`, `"Animated"`. Prefer `Animated:false`, `Type:glb/obj`.
- **Download:** plain GET of the `.glb` URL (browser UA). No auth, no expiry.
- **Scale warning (verified):** Poly Pizza models are real-world scale — the
  test wind turbine is 38×77×10 m. ALWAYS place via `prop()`/`kitClone()`
  with an explicit target height; never place raw. Bases are often below
  y=0 (`prop()` compensates from the bbox — do not pre-offset by hand).
- **Official API** (`/docs/api/v1.1`) exists but needs an account key; the
  HTML flow above needs none, so the skill uses HTML.

## Adding a new source

A source earns a guide section when it is verified end to end: search →
preview → download → Gate 1 → three.js load → still. Document the URL
patterns, auth/headers, folder layout, texture rules, licence range, and one
worked example with measured sizes. Unverified sources don't go in the skill.

## Fetch-then-create ladder

1. Local cache hit → copy, place, done.
2. Kenney kit model → fetch, gate, cache, place (best style match).
3. Poly Pizza single → fetch, gate, cache, place (best coverage).
4. Procedural (`build.ts` boxes/batches, VEG-style) → only when 1–3 fail,
   with the reason on the prop-list line. Hero/story-specific geometry
   (bridges, machines that deform) usually lands here by nature.

## Landmines (placing — learned the hard way)

- Shot-specific furniture hides outside its shots (per-shot visibility groups):
  a static table wandering into wides reads as a random table. Every visible
  prop must earn its frame.
- Every fx card ties to a timed event (word/beat) — a continuous twinkle reads
  as random floating junk (`fx_gate.py` enforces word-ties + durations).
- Unmapped GLB material names fall back to source colors — extend `RECOLOR`
  deliberately instead (`material_check.py` fails unmapped names).
- Hand-computed screen positions are sign-error-prone: verify all framing
  empirically (`ndc_check.mjs`), always.
- Effect cards pasted on geometry (a map on a board) need a world-locked yaw:
  camera billboards visibly float off the surface at oblique angles.
  Free-floating effects stay billboards.
