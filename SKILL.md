---
name: cartoon-3d-short
description: Make a ~55-70 s vertical cartoon story short in the "2D characters in a colourful 3D world" style (flat bean-head cartoon cards with ink outlines, painted 3D town/world with black ink lines, saturated sky, depth-of-field backgrounds, gliding cameras, voice narration, synthesized SFX + march-style music), rendered with three.js inside Remotion. Proven on "The Bridge That Fell for a Song" (2026-10-31). Use when the user asks for another video "like the bridge video", "like the soldiers/bridge short", "in that cartoon 3D style", a history/science story short with cartoon characters in 3D, or says "use the cartoon short skill".
---

# Cartoon 3D story short (three.js + Remotion)

Proven example: **The Bridge That Fell for a Song** (67 s, 1831 Broughton bridge, 74 soldiers): code in `src/videos/bridge/` (`BridgeShort`, 1080x1920, 30 fps); script/voice/sound in `~/bridge-short/`; style research in `references/`.

The style reference is a channel studied privately (`references/`: STYLE_BIBLE.md, reports/*.md, frames/).
- Those videos are private study material. Never upload, publish or send them.
- Never copy their scripts, characters or shots. Story, characters and voice are always OUR OWN.
- Never say the channel's name in a voice-over or description.

User rules that apply:
- No time pressure exists. Never take a shortcut to save time or effort: every deliverable is production grade — run all gates, fix root causes, verify with evidence. When a choice trades quality for speed, quality wins without asking.
- Story first, always: build or fetch assets, worlds, kits and sets according to the story — never morph the story to fit whatever scenes or worlds already exist. If a beat needs a place that does not exist yet, that place gets designed or fetched; reusing the street set for it is a failure, not a shortcut. Never merge two story places into one set to save a setup — a new isolated setup is never a shortcut violation, and build cost never justifies a composite.
- Captions ship in every video (Hormozi style, step 10) unless the user opts out. No other labels.
- English only.
- Voice: locked Turbo-male expressive style (step 3), all videos.
- Jokes are researched real facts.
- Standard mix: music +3 dB, SFX -6 dB, voice unchanged.
- Final export 2K vertical: 1440x2560, `--scale 1.3333333333333333` (full precision: 1.3333 yields
  fractional pixels and Remotion 4 rejects it; the long form multiplies to exactly 1440x2560).
- Opus max verifies every check.
- Save after every step.
- "Just do it" once the script is approved — it skips the human, never the self-review gates.
- Illustrate the meaning, not the words (see STAGING.md). Literalism is the default failure mode — and it is gated, not advised: the brief schema forces meaning/absent/entrances declarations, `continuity_lint.py` enforces a noun-coverage ceiling and bans composite metaphors, and nothing may be visible before its cause (presence tags + intro shots, step 4).

## Pipeline
1. **Topic and facts.** Pick one surprising true story with a physical cause and effect (it should be visual), plus a simple everyday analogy that explains it.
   - Write the facts with their source at the top of `SCRIPT.md`.
2. **Script** (~3.7 words/s, 55-70 s). Beat formula from the bridge short:
   - **Hook:** the absurd fact in one line ("Seventy-four soldiers knocked down an iron bridge just by walking across it.").
   - **Setting:** year, place, pride.
   - **Action:** escalation over three or four beats, each a little bigger.
   - **Snap:** the moment it breaks.
   - **Deadpan double line:** "Luckily ... / Unluckily ...".
   - **Explanation:** one physics idea through an everyday analogy (the kid on a swing).
   - **Consequence:** the rule it created.
   - **Callback twist:** the ending.
   - Never describe on screen what the viewer already sees.
3. **Voice.** `SKILL` = the folder this SKILL.md is in. Once per computer: `bash SKILL/templates/voice/setup_voice.sh`
   until it prints **Voice setup OK** (private env `~/.cartoon-3d-short/venv`; Kokoro voice ~340 MB, Whisper small.en
   ~0.5 GB, all local and free; narration runs on the NVIDIA GPU when present, else CPU). The standard narration for
   every video is the locked Turbo-male expressive style (set 2026-11-14 from the cobra voice tests): Chatterbox Turbo
   cloning a Kokoro `bm_george` reference, one CUT per line, `exaggeration=0.6, cfg_weight=0.5, temperature=0.8,
   norm_loudness=False` (`True` upcasts the ref to float64 and crashes in stft); assembly `lead 0.2 / gap 0.25 /
   outro 0.3`, peak 0.9; emphasis shaping: `!` on the hook + stakes lines, em-dash pause in the hook. The reference
   clip is the full script rendered first with `bm_george` x1.15 (doubles as the timing draft). Chatterbox needs a
   torch-CUDA env with `chatterbox-tts` (torchaudio build must match torch's CUDA, e.g. the cu128 index; read/write
   audio with scipy, not torchaudio, unless torchcodec is installed). Before anything is timed to the narration, the
   pronunciation gate must PASS:
   `SKILL/templates/voice/py SKILL/templates/voice/pron_check.py <project>/voice_work/`
   (Whisper transcribes, every script word is aligned; number phrases, hyphen splits and HOMO homophones compare
   canonically). Fix ladder for flags, cheapest first: `speak.json` respelling (`clerks`->`clurks`), comma/period to
   force a boundary, re-render ONLY the flagged lines, chunk-split one display line into two TTS takes for swallowed
   words (display/captions unchanged); Whisper's own misspellings go in `allowlist.json`. `--dump FROM TO` prints raw
   heard tokens for diagnosis. faster-whisper CUDA can fail at transcribe time — `words.py` retries on CPU there too.
   `voice_work/` adapter: per-line wavs + `narration.wav` + `lines.json` + `script.json`, so `words.py` runs unchanged.
   Output: `voice.wav` (48 kHz mono), `words.json` (`[{w,s,e}]`), `words.txt` + `lines.json` for checking.
   - No Chatterbox on this machine: fall back to `render_narration.py lines.txt <project>/voice/ --dur 67.5 --speed 1.15`
     (Kokoro `bm_george` x1.15, the pace standard); the pron gate still applies.
   - Own recording instead: same fallback command with `--audio their.m4a` (Whisper rebuilds the timings from it).
   - No voice yet: `--estimate` previews the timing (stdlib only; re-run without it when the voice exists).
   - Hand-fix the word timings against words.txt. Everything is timed to words.json.
4. **Scene briefs, then shot plan.** FIRST read `STAGING.md` and write `briefs/shot_<id>.md` for every beat (three staging options + pick rationale each, all depth layers filled, reaction character with a counter-emotion, ≥1 word-timed story event; the schema also demands meaning/absent/entrances/knows/teaches/turn-mechanism/metaphor — a brief that depicts every noun in its sentence is rejected before any option is weighed). Then render blockout previs (`PREVIS=1 ... node scripts/bridge-stills.mjs out/<name>/previs/x_ <first,mid,last frames> 0.25`) and get composition approved. No `story.ts` code until briefs + previs pass. Seed `out/<name>/shot_manifest.json` from the briefs (entities/layers/events per shot; example in `templates/briefs/`) — `shot_lint.py` gates the final render on it, and every entity it counts must also pass `continuity_lint.py` (floors count motivated entities only). Write the continuity ledger `out/<name>/continuity.json` from the briefs (sets, entity homes + intro shots, per-shot presence tags `entered`/`resident`/`cut-in`, audience knows/teaches, depicts/nouns, metaphor staging; example in `templates/briefs/`) — `continuity_lint.py` gates the final render on it: no teleports (location change without travel), nothing visible before its cause (no presence before its intro shot), no residents outside their home set, no merged places (residents of two sets sharing one setup), noun coverage ≤ 0.8 per shot, metaphors staged as cut sequences only. If either lint fails later, the brief was fiction — fix the scene, not the manifest. Write the prop list (`props/<name>.md`: shot → object → set → cached/fetch/create) from the briefs' foreground/midground/background slots — if no brief names it, it doesn't get fetched. Then in `story.ts`: copy `templates/bridge/` (the final bridge source, same as `src/videos/bridge/` of your Remotion project) to `src/videos/<name>/`, register a new composition next to `BridgeShort` in `src/Root.tsx`, and rename it
   (component, `*_FRAMES` const, delayRender label). New story, new world: rewrite `story.ts` fully (shots/cameras/DOF),
   replace `buildTown`'s layout, rewrite `cast.ts` roles (keep its Pool/Actor/Fx/person/blob machinery), and strip
   `world.ts` to sky/lights/clouds/smoke/cast-loop plus your props. Shot-specific props (anything that must appear or
   vanish mid-film) live as world.ts groups with per-shot visibility — never in the merged static batch.
   - Tag every shot INT or EXT at plan time, from the story facts, before building anything. The slugline test: if the
     real action happened IN something (a courtroom, a shed, a lab, a vehicle — under a roof), it is INT, full stop.
     Further INT triggers: the beat needs furniture that only makes sense inside (a judge's bench); secrecy or privacy
     is story-relevant (scheming, cover-ups); the "sidewalk absurdity" test fails (a judge's bench on the pavement is
     absurd — that feeling is the signal). Never downgrade INT action to a street board because the street set exists.
   - INT staging is dollhouse style (user-locked house style) — full spec in `STAGING.md`.
   - `SHOTS`: id, a/b frames, light day/golden, crowd mode, `tau` story time.
   - `XFADE`: crossfades at place/time changes.
   - `FLASH_AT`: a white flash after the hook; later impacts get a `FLASH2` map (frame -> frames).
   - `CAMS`: per-shot keys `{f, dur?, cut?, s: f => {pos, look, fov, roll}}`.
   - `TURN`: every shot's turn declares `cut` or `in-shot move` in its brief. Any change of place, time, or subject across the turn is a cut (`XFADE` counts); in-shot moves serve emphasis inside one continuous moment only. Panning to a pre-placed element the story has not motivated is a rejected brief — see STAGING.md camera grammar. One shot, one set: a shot's turn never spans two places.
   - `KICKS`: impact flip-shakes.
   - `DOF`/`dofAt`: lens blur per beat.
   - `FOREGROUND`: near framing props.
   - Every visual reaction lands 0-3 frames before its word.
5. **World.** Read `ASSETS.md`: fetch-first props (`fetch_assets.py` — local cache → Kenney / Poly Pizza → Gate 1 → cache; procedural only when fetching fails, with the reason on the prop-list line). Copy cached models into `public/<video>/` (never re-download a cached model); Gate 2 (looks right) is the source preview first, the scene still finally. Look values in `LOOK.md`; run `material_check.py` before dressing sets.
   - `lights.ts`: LIGHTS plus the LOOK sky/river/cloud palette per light.
   - `shade.ts`: two-tone shading and `untone()`.
   - `build.ts`: town, houses and fetched kit props, recoloured, with sight-line culling of anything blocking a camera.
   - `paint.ts`: HD Canvas2D painted textures with seams painted in as dark tints.
   - `world.ts`: sky shader, fog = horizon colour, river, per-frame posing, sun frozen per shot and camera-relative.
6. **Characters.** Read `ACTING.md` and `CHARACTER_DESIGN.md` first. Write `characters/<name>.md` briefs (shape language, silhouette, signature prop, 3 distinguishing features, posture/gait); render turnaround + 6-expression sheets and PASS `python scripts/silhouette_check.py out/<name>/silhouettes/*.png` before any scene uses a character. Faces are parametric (`face_rig.ts` presets + blends, asymmetric allowed): every lead performance is an emotion timeline (anticipation → peak with overshoot → settle, keys 0-3 f before the word) with body acting in the same keys (lean, squash, head tilt, arm pose); dialogue mouths follow `words.json` via `mouthFromWords()`; quantize faces (`quantizeFace()`, ≤12 distinct lead faces / ≤8 crowd faces per shot) so the canvas pool holds.
   - `toon.ts`: the Canvas2D `Pen` drawing API, 600x1000 design canvas, soles at y = 975, bean heads, stick limbs, plum variable-width outline, face library.
   - `face_rig.ts`: `FaceParams`/`BodyPose`, preset blends, emotion tracks, voice-driven mouths.
   - `cast.ts`: camera-facing billboards, crowds, effect cards, blinks, walk cycles. All billboards go on the `NOINK` layer. Pass quantized `face`/`body` in `FrontOpts`/`SideOpts` (they enter the pool key automatically).
   - `cardshade.ts`: cards lit by the scene light, no emissive.
7. **Post** (`Bridge.tsx` + `ink.ts` + `lensblur.ts` + `grade.ts`; values + landmines in `LOOK.md`).
   - Composer order: ink → lens pre → lens main → bloom → NEUTRAL tone map → grade (MSAA 4).
   - Every pixel parameter scales with output height / 1920.
8. **Sound** (`~/bridge-short/audio/`: timeline.py, sfx_gen.py, sfx.py, music.py, instruments.py, dsp.py, mix.py).
   - Event table → synthesized SFX plus an original score ducked under the voice.
   - Output: mix.wav (48 kHz, exact length), stems and cues.md.
   - New story, new score: reuse `dsp.py` / `instruments.py` / `sfx_gen.py` and the render/mix machinery as-is;
     recompose `timeline.py` (picture mirror), `music.py` build + SECTIONS, `sfx.py` cues, and the mix's MUSIC_TARGET.
   - The SFX stem scales to the voice (`v_ref`): any new voice invalidates the cached SFX stem — delete and re-render it.
   - Lock the picture's time constants before the sound is made. Any later timing change means re-running the sound.
   - An SFX cue exists only once measured: check each family's band energy in its windows vs control windows (hisses sit ~-7.5 LU: above music, below narration).
9. **Look checks.** Run `node scripts/bridge-stills.mjs out/<name>/x_ 100,400 0.5`.
   - Set `BRIDGE_ENTRY=src/sandboxes/<n>/index.tsx` to render a sandbox copy.
   - Make side-by-sides against reference frames with `python scripts/sbs_sheet.py out.jpg --ours ... --ref ...`.
   - Send them to an Opus max verifier: 1-3 images, a ≤200-word verdict.
   - Placement: declare relations, not coordinates — `placeOn`/`inside`/`attach` from `placement.ts` with shared `SOCKETS` (world.ts and cast.ts import the same constants); resting heights resolve by raycast; foot lock on planted feet.
   - Geometric audit (machine pass after the look is right; pixel QA cannot see a head inside a pot wall): export `out/<name>/geo_manifest.json` during stills (every ~10th frame PLUS every contact-event frame: lid lift, slam, tip) and run `node scripts/geo_audit.mjs out/<name>/geo_manifest.json` until it PASSES — ground gaps, passthrough, container containment + rims, face sightlines vs all geometry (decks/beams/roofs, not just columns), face boxes vs caption strip and frame edges, billboard foot offsets. Debug renders: top-down orthographic + wide side view with collider boxes and foot markers drawn on. Then prove each contact with a targeted still on the exact frames and re-verify after every fix. The burial check covers CAST too: an actor placed inside architecture (v1 molasses parked its S3 worker inside the tank cylinder) is silently swallowed by the wall — prove every credited actor visible in at least one still, never by coordinates alone.
   - Camera/framing/fx machine checks (same stills pass): `camera_audit.mjs` (lens path vs geometry, near-plane subjects), `ndc_check.mjs` (every credited face framed + visible somewhere), `fx_gate.py` (every fx tied to a word, bracketed stills on disk).
   - Continuity review (single stills structurally cannot show cross-shot nonsense, so review pairs, never singles alone): for every cut, a side-by-side of shot N's last frame + shot N+1's first frame; verify entrances read (nobody pops in), nobody vanishes without exiting, and each shot's residents were either visible before or are introduced by the cut. Empty-frame fix ladder, cheapest first: reframe the move, cut away and back, restage the action — ADDING an element to a frame is last, and any added element must update `continuity.json` with its motivation the same turn or `continuity_lint.py` fails the build. Dense frames are not better frames.
   - Defect ledger: `python scripts/defect_ledger.py out/<name>/defects.json init` at the first look check; log every bug the turn it is found (`add` with a before-crop); fix per shot (render the shot, not the film, so a fix costs seconds); every fix needs a before AND after crop at the same frame (`fix`), re-checked (`verify`); `gate` must PASS before the final render. VLM critique is capped at 3 rounds per defect — programmatic checks first, and too many iterations degrade the result. Use class `sense` for spatial/causal nonsense (unmotivated presence, teleport, composite metaphor, pan-to-pre-placed).
10. **Captions (in every video).** Hormozi style, from `templates/captions.tsx` + the voice's `words.json`
    (single source of truth): Montserrat ExtraBold, ALL CAPS, white with a thick black outline
    (`WebkitTextStroke` ~11% of font size, `paintOrder: "stroke fill"`); each page pops in as a unit (5-7 words at
    Kokoro pace, fewer at slower Turbo pace — longer words per window, cap 5 not 6)
    (page-level spring, hard cuts); only the yellow (`#FFEA00`) highlight travels with the narration — never
    animate words in one by one (rejected as too distracting). Bottom-center (`paddingBottom` 330, `maxWidth` 980
    at the 1080x1920 design size). Needs `@remotion/captions` (same version as remotion) and
    `public/fonts/Montserrat-ExtraBold.woff2` (Google Fonts latin subset); the component holds a delayRender
    handle until the FontFace loads, else frames render in a fallback font. Never more than two lines: page by
    ~1.7 s windows (`combineTokensWithinMilliseconds: 1700`, silence breaks, hard cap 6 balanced tokens so no
    chunk strands an orphan word) and prove the cap by measuring EVERY page with the real woff2 over every
    active-word case, including stroke bleed into the gaps — not by eyeballing stills. Caption pages pop pixels at once:
   fold every page-start frame (±1) into `shots.json` "planned" so QA pops only fire on real glitches.
11. **Final render (GPU).**
    - Gates — ALL must PASS before the render starts: pron gate (step 3), `kit_check.py`, `shot_lint.py` (+ `perframe.npz`), `continuity_lint.py`, `geo_audit.mjs`, `camera_audit.mjs`, `ndc_check.mjs`, `fx_gate.py`, `perf_budget.py`, `material_check.py`, `silhouette_check.py`, `caption_audit.py`, `focus-audit`, defect-ledger `gate`.
    - `npx remotion render src/index.ts <Comp> out/<name>/video.mp4 --codec h264 --crf 16 --scale 1.3333333333333333 --gl=vulkan --concurrency=2 --timeout=180000`
    - `--gl=vulkan` = NVIDIA (ANGLE-on-Vulkan), `--gl=angle-egl` = Intel iGPU. `--gl=egl` can NOT make a WebGL context: never use it.
    - Concurrency ceiling on a 6 GB card: 2 is fastest RELIABLE; 4+ loses GL contexts (blank frames), 8+ renders all white. Verify any new value with a flat-frame scan before trusting it.
    - Keep `--crf 16` libx264 (NVENC forbids CRF; encode runs concurrently and is never the bottleneck).
    - Budget: 2K renders run ~4 fps (≈10 min for 67 s); stills at 0.5 take 3-8 s each after a ~40 s bundle.
    - Mux with `-map 0:v:0 -map 1:a:0` (Remotion writes a silent audio track).
    - QA: `python scripts/short_qa.py final.mp4 out/<name>/qa shots.json` checks every frame for black, white, frozen and pop frames, plus loudness and sheets. Account every pop against the plan (kick, burst, cut, fast glide) before touching anything.
    - Disk: every bundle copies `public/` (~1.3 GB) into temp and never deletes it — always render with `TEMP`/`TMP` on a big drive (forward slashes in JS strings), and sweep finished projects' `remotion-webpack-bundle-*` folders (ask first).
    - Fix anything it finds, then run a deep Opus audit.
12. **Deliver.** SendUserFile the final mp4, update memory, write notes.

## Changelog
- 2026-11-17: continuity update (from the Emu War post-mortem). Added: no-shortcuts principle; continuity ledger + `continuity_lint.py` gate (presence tags, teleports, intro shots, merged places, noun-coverage ceiling, metaphor-as-sequence); brief schema fields (meaning/absent/entrances/knows/teaches/turn-mechanism/metaphor); cut-default camera grammar; neighbor-pair stills review; `sense` defect class.

## Guides (load at the step that needs them)
- `STAGING.md` — step 4: scene briefs, staging patterns, previs. Camera landmines live here.
- `ACTING.md` — step 6: parametric faces, emotion timelines, body acting, pool budget.
- `CHARACTER_DESIGN.md` — step 6: character briefs, silhouette gate.
- `ASSETS.md` — step 5: fetch-first props, source guides, 2 accept gates, cache.
- `LOOK.md` — steps 5/7/9: look values, look targets, look-match loop, post landmines.
