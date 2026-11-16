---
name: cartoon-3d-short
description: Make a ~55-70 s vertical cartoon story short in the "2D characters in a colourful 3D world" style (flat bean-head cartoon cards with ink outlines, painted 3D town/world with black ink lines, saturated sky, depth-of-field backgrounds, gliding cameras, voice narration, synthesized SFX + march-style music), rendered with three.js inside Remotion. Proven on "The Bridge That Fell for a Song" (2026-10-31). Use when the user asks for another video "like the bridge video", "like the soldiers/bridge short", "in that cartoon 3D style", a history/science story short with cartoon characters in 3D, or says "use the cartoon short skill".
---

# Cartoon 3D story short (three.js + Remotion)

Proven example: **The Bridge That Fell for a Song**. It is an original 67 s short about the 1831 Broughton bridge and 74 soldiers marching in step.
- Code: `src/videos/bridge/` of your Remotion project (composition `BridgeShort`, 1080x1920, 30 fps).
- Script, voice and sound: `~/bridge-short/`.
- Style research: `references/`.

The style reference is a channel studied privately (`references/`: STYLE_BIBLE.md, reports/*.md, frames/).
- Those videos are private study material. Never upload, publish or send them.
- Never copy their scripts, characters or shots. Story, characters and voice are always OUR OWN.
- Never say the channel's name in a voice-over or description.

User rules that apply:
- Story first, always: build or fetch assets, worlds, kits and sets according to the story — never morph the story to fit whatever scenes or worlds already exist. If a beat needs a place that does not exist yet, that place gets designed or fetched; reusing the street set for it is a failure, not a shortcut.
- Captions ship in every video (Hormozi style, step 10) unless the user opts out. No other labels.
- English only.
- Voice: locked Turbo-male expressive style (step 3), all videos.
- Jokes are researched real facts.
- Standard mix: music +3 dB, SFX -6 dB, voice unchanged.
- Final export 2K vertical: 1440x2560, `--scale 1.3333333333333333` (full precision: 1.3333 yields
  fractional pixels and Remotion 4 rejects it; the long form multiplies to exactly 1440x2560).
- Opus max verifies every check.
- Save after every step.
- "Just do it" once the script is approved.

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
   heard tokens for diagnosis.
   Output: `voice.wav` (48 kHz mono), `words.json` (`[{w,s,e}]`), `words.txt` + `lines.json` for checking.
   - No Chatterbox on this machine: fall back to `render_narration.py lines.txt <project>/voice/ --dur 67.5 --speed 1.15`
     (Kokoro `bm_george` x1.15, the pace standard); the pron gate still applies.
   - Own recording instead: same fallback command with `--audio their.m4a` (Whisper rebuilds the timings from it).
   - No voice yet: `--estimate` previews the timing (stdlib only; re-run without it when the voice exists).
   - Hand-fix the word timings against words.txt. Everything is timed to words.json.
4. **Shot plan** in `story.ts`: copy `templates/bridge/` (the final bridge source, same as `src/videos/bridge/` of your Remotion project) to `src/videos/<name>/`, register a new composition next to `BridgeShort` in `src/Root.tsx`, and rename it
   (component, `*_FRAMES` const, delayRender label). New story, new world: rewrite `story.ts` fully (shots/cameras/DOF),
   replace `buildTown`'s layout, rewrite `cast.ts` roles (keep its Pool/Actor/Fx/person/blob machinery), and strip
   `world.ts` to sky/lights/clouds/smoke/cast-loop plus your props. Shot-specific props (anything that must appear or
   vanish mid-film) live as world.ts groups with per-shot visibility — never in the merged static batch.
   - Tag every shot INT or EXT at plan time, from the story facts, before building anything. The slugline test: if the
     real action happened IN something (a courtroom, a shed, a lab, a vehicle — under a roof), it is INT, full stop.
     Further INT triggers: the beat needs furniture that only makes sense inside (a judge's bench); secrecy or privacy
     is story-relevant (scheming, cover-ups); the "sidewalk absurdity" test fails (a judge's bench on the pavement is
     absurd — that feeling is the signal). Never downgrade INT action to a street board because the street set exists.
   - INT action is staged dollhouse style (the user-locked house style): open-faced room boxes — floor + back wall +
     two side walls, no front wall, no ceiling — with the EXT camera outside looking in (this is exactly the film
     convention: scene inside + camera outside still shoots as exterior coverage). Build one room per INT location as
     a per-shot-visible world.ts group on a separate stage apron away from the town (never embedded in a house row),
     so sight-lines, the culler and roofs can never interfere. Sunlight rakes in through the open face as usual; add a
     warm practical only for evening interiors. Camera grammar is unchanged (the lens never enters the room); INT/EXT
     changes are always hard cuts. Verify in stills: open face toward the lens, no roof or ceiling in frame, back wall
     dressed (never a bare flat plane).
   - `SHOTS`: id, a/b frames, light day/golden, crowd mode, `tau` story time.
   - `XFADE`: crossfades at place/time changes.
   - `FLASH_AT`: a white flash after the hook; later impacts get a `FLASH2` map (frame -> frames).
   - `CAMS`: per-shot keys `{f, dur?, cut?, s: f => {pos, look, fov, roll}}`.
   - `KICKS`: impact flip-shakes.
   - `DOF`/`dofAt`: lens blur per beat.
   - `FOREGROUND`: near framing props.
   - Every visual reaction lands 0-3 frames before its word.
5. **World.**
   - `lights.ts`: LIGHTS plus the LOOK sky/river/cloud palette per light.
   - `shade.ts`: two-tone shading and `untone()`.
   - `build.ts`: town, houses and Kenney CC0 kit props, recoloured, with sight-line culling of anything blocking a camera.
   - `paint.ts`: HD Canvas2D painted textures with seams painted in as dark tints.
   - `world.ts`: sky shader, fog = horizon colour, river, per-frame posing, sun frozen per shot and camera-relative.
6. **Characters.**
   - `toon.ts`: the Canvas2D `Pen` drawing API, 600x1000 design canvas, soles at y = 975, bean heads, stick limbs, plum variable-width outline, face library.
   - `cast.ts`: camera-facing billboards, crowds, effect cards, blinks, walk cycles. All billboards go on the `NOINK` layer.
   - `cardshade.ts`: cards lit by the scene light, no emissive.
7. **Post** (`Bridge.tsx` + `ink.ts` + `lensblur.ts` + `grade.ts`).
   - Composer order: ink → lens pre → lens main → bloom → NEUTRAL tone map → grade (MSAA 4).
   - Every pixel parameter scales with output height / 1920.
8. **Sound** (`~/bridge-short/audio/`: timeline.py, sfx_gen.py, sfx.py, music.py, instruments.py, dsp.py, mix.py).
   - Event table → synthesized SFX plus an original score ducked under the voice.
   - Output: mix.wav (48 kHz, exact length), stems and cues.md.
   - New story, new score: reuse `dsp.py` / `instruments.py` / `sfx_gen.py` and the render/mix machinery as-is;
     recompose `timeline.py` (picture mirror), `music.py` build + SECTIONS, `sfx.py` cues, and the mix's MUSIC_TARGET.
   - The SFX stem scales to the voice (`v_ref`): any new voice invalidates the cached SFX stem — delete and re-render it.
   - Lock the picture's time constants before the sound is made. Any later timing change means re-running the sound.
9. **Look checks.** Run `node scripts/bridge-stills.mjs out/<name>/x_ 100,400 0.5`.
   - Set `BRIDGE_ENTRY=src/sandboxes/<n>/index.tsx` to render a sandbox copy.
   - Make side-by-sides against reference frames with `python scripts/sbs_sheet.py out.jpg --ours ... --ref ...`.
   - Send them to an Opus max verifier: 1-3 images, a ≤200-word verdict.
   - Placement/passthrough audit (separate pass after the look is right; pixel QA cannot see a head inside a
     pot wall): for every DYNAMIC object list what it can touch (lids vs heads, pots vs necks, feet vs ground,
     stacked bodies) and every STATIC group vs the set (nothing buried in walls: the shed swallowed half the
     cobra yard); check ground contact (resting y >= surface), container containment (contents inside while
     lids shut; grow/rise choreography must clear rims, verified frame by frame), and motion bounds (sway/crawl
     amplitudes keep clearances); prove each contact with a targeted still on the exact frames (lid lift, slam,
     tip) and re-verify after every fix. The burial check covers CAST too: an actor placed inside architecture
     (v1 molasses parked its S3 worker inside the tank cylinder) is silently swallowed by the wall — prove every
     credited actor visible in at least one still, never by coordinates alone.
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
    active-word case, including stroke bleed into the gaps — not by eyeballing stills.
11. **Final render (GPU).**
    - `npx remotion render src/index.ts <Comp> out/<name>/video.mp4 --codec h264 --crf 16 --scale 1.3333333333333333 --gl=vulkan --concurrency=2 --timeout=180000`
    - `--gl=vulkan` = NVIDIA (ANGLE-on-Vulkan), `--gl=angle-egl` = Intel iGPU. `--gl=egl` can NOT make a WebGL context: never use it.
    - Concurrency ceiling on a 6 GB card: 2 is fastest RELIABLE; 4+ loses GL contexts (blank frames), 8+ renders all white. Verify any new value with a flat-frame scan before trusting it.
    - Keep `--crf 16` libx264 (NVENC forbids CRF; encode runs concurrently and is never the bottleneck).
    - Mux with `-map 0:v:0 -map 1:a:0` (Remotion writes a silent audio track).
    - QA: `python scripts/short_qa.py final.mp4 out/<name>/qa shots.json` checks every frame for black, white, frozen and pop frames, plus loudness and sheets.
    - Fix anything it finds, then run a deep Opus audit.
12. **Deliver.** SendUserFile the final mp4, update memory, write notes.

## Final look values (bridge after 4 verifier rounds; all in `templates/bridge/`)
Start every new short from `templates/bridge/` (copy to `src/videos/<name>/`): the look lives in these values, the
story lives in story.ts / build.ts layout / cast.ts roles. Opus max scores at the end: colour day 7, golden 5-6,
lighting 5-6, ink 6, textures 5-6, characters 7, depth 6-7, composition 6-7 (from 5/3/4/5/4/7/4/6 at the start).
- **Light presets** (`lights.ts`, sun camera-relative and frozen per shot):
  - day: az 75 / el 48, lit [1.58,1.5,1.33], shade [.30,.29,.36], lift [.05,.06,.11] (cool tint ONLY in shade), sky
    top #3e7fd2 → horizon #b8d0ec, fog = horizon, 25→300 m, uSat 1.08, ~15 % blue haze past 60 m.
  - golden: az 6 / el 7 (backlit low sun), key toward #FFB36B ×1.5, violet-blue shade (facade ≈ #444380), sky
    #ffc47c → #8a6f8a, peach fog only past 50 m, sun disc #ffcf9e + bloom, contact blobs + real card shadows.
- **Albedos** (`paint.ts`/`build.ts`): muted brick / cream / ochre / terracotta houses with plinth, cornice, sills,
  hoods, door step, chimney + pot, heights 7 / 8.4 / 9.8 m; warm grey/beige stone (saturation −35 % from "storybook");
  ochre wood deck C* ~51-58 with near-black seams; iron dark and desaturated. Never lemon, never lavender lit faces.
- **Ink** (`ink.ts`): #030303, 5.1 px near (6 m) → 3.3 px far (90 m) at 1080x1920, creases ×0.8 from 35°, depth
  jumps from 1 %, fog tint 0.3 only far; character cards on layer `NOINK` (they carry their own plum ink).
- **Lens** (`lensblur.ts` + `dofAt` in story.ts): cInf px at 1080: hook/river CU 15-16, close-ups 12-14, MS 10-12,
  park 7, golden sway 5, wides/aerials 0. Focus on the eyes of the front row — ALWAYS the cast, never the set:
  v2 molasses shipped six shots of soft characters because the table focused look points and tank walls while the
  cast stood off-plane. Gate: `npm run focus-audit` (predicted CoC per credited face, ≤5px) must pass before the
  final render, and face sharpness is then confirmed on full-resolution crops, never on 540px stills.
- **Post** (`Bridge.tsx`): ink → lens pre → lens main → bloom (thr 1.0, int .5, 6 levels, radius .6) → NEUTRAL tone
  map → grade; MSAA 4. Film grain exists but is OFF (reference measures no grain; it quadruples the file size).
- **Characters** (`toon.ts`/`cast.ts`/`cardshade.ts`): bean heads h/w .94, plum ink #241726, eyes .26 W apart, no blush,
  14 expressions; adults 3.5 head-heights; walk bob 5 %, lean 1-7°, planted 0.8 m stride; blinks 0.5-2.3 s; tight
  contact shadow ~.5 under the feet + sun-direction tail by day; golden rim inner only (never an offset outer copy).
- **Camera** (`story.ts`): cuts on big jumps, smootherstep glides 18-40 f, every hold creeps (no static hold ≥4 f),
  flip kicks decaying over 7 f on impacts, 4-4.6° rolls, foreground props (`FOREGROUND`) in ~1/3 of shots.

## Look targets (measured from the reference; see references/reports/)
- **Ink:**
  - World lines: about 3 px at 1080 wide, near-black #0b0a0c, nearly constant with distance. Silhouettes, depth jumps and normal creases only. No line on wall/floor joins or the horizon. Character cards are never outlined by the world ink.
  - Character ink: dark plum #201628-#2f1d28, thicker on the bottom/shadow side.
- **Colour:**
  - Day median luma ~.57. Non-ink p5 ~.23 (no crushed blacks). Lit chroma C* p90 ~55. Day sky top ~#5e93d9, horizon 1.28x brighter.
  - Golden: peach horizon #ffd08a, violet-blue shadows (never brown), backlit sun.
- **Depth:**
  - DOF on about 1/3 of screen time (CU, MS, inserts), cInf 10-16 px at 1080, focus on the eyes. Establishing and wide shots stay sharp.
  - Fog = horizon colour, 25→420 m day, 20→360 m golden.
  - Bloom only on HDR emissives: threshold 1.0.
- **Camera:**
  - Hard cuts on big jumps. Everything else is a smootherstep glide of 18-40 f, peak ≤ 25 px/f at 720p.
  - Every hold pushes in 0.15-0.35 %/f, with 0.6 %/f on punch words.
  - Rolls of 4-5°.
  - No hand-held float. Impact shakes flip sign every frame and decay over 7 f.
- **Characters:**
  - About 3.5 head-heights tall, legs 1.4 HH.
  - Stick limbs about 0.055 of head width, ink-dot hands.
  - Bean head (h/w ~0.93, narrower chin, pointier crown).
  - No blush or eye highlights. Faces at brightness ~.93.
  - Walk bob 3-7 %, lean 1-7°, planted feet.
  - Blinks every 0.5-2.3 s, lasting 4 f.

## Look-match loop (how the bridge look was reached; reuse for any "make it look like X" pass)
1. **Measure the reference first.** One analysis agent per topic (motion, depth, textures, characters, lighting, outlines, grade), each writing numbers, not adjectives, to `references/reports/<topic>.md`. Shared brief: `compare/CONTEXT.md`. Reports are the source of truth for every agent after.
2. **Sandboxes, one owner per file.** Copy the project folder to `src/videos/<name>_{cam,world,mat,char,post}` with entries `src/sandboxes/<n>/index.tsx` (same `index.tsx` as main, only the import path changed). Ownership used for the bridge:
   - cam: story.ts (camera keys, cuts, kicks, DOF table, foreground props)
   - world: world.ts, lights.ts, shade.ts, grade.ts (sun, sky, fog, river, colour, grade)
   - mat: paint.ts, build.ts (painted textures, buildings, props)
   - char: toon.ts, cast.ts, cardshade.ts (character drawing, posing, card lighting, fx cards)
   - post: ink.ts, Bridge.tsx, lensblur.ts (outline pass, composer, lens blur, bloom)
   Agents only edit their own files in their own sandbox and render stills with `BRIDGE_ENTRY=src/sandboxes/<n>/index.tsx node scripts/bridge-stills.mjs out/<name>/<n>/x_ <frames> 0.5`.
3. **Merge** with `python scripts/bridge_merge.py [cam,world,mat,char,post]` (backs main up to `backup/bridge_<time>/`, copies owned files only). Then `npx tsc --noEmit` (filter to the project folder), then **re-sync every sandbox from main** (`cp -f src/videos/<name>/* src/videos/<name>_<n>/`) before the next round.
4. **Verify** with a fresh Opus max agent: side-by-side sheets (`python scripts/sbs_sheet.py out.jpg --ours a b --ref r1 r2`), score each area out of 10 (colour day / golden, lighting, ink, textures, characters, depth, composition) plus a numbered fix list with frame numbers. Map each fix to the file owner and resume that owner's agent with SendMessage (keeps its context). Bridge scores: round 1 5/3/4/5/4/7/4/6 → round 2 5/4/5/6/4/7/6/6 → round 3 see notes.
5. Contracts between owners live in exported constants (e.g. `NOINK` layer from ink.ts, `dofAt`/`FOREGROUND` from story.ts, `LIGHTS`/`LOOK` from lights.ts). Changing a contract means telling every owner that reads it.

## Gotchas
- Kenney nature-kit materials are teal: recolour them by material name in build.ts.
- Cameras end up inside houses: the sight-line culler in build.ts/world.ts removes anything blocking any camera ray.
- Ink in the same merged effect pass as DOF gets overwritten. Ink must be its own pass before the blur.
- Never put `dispose={null}` on a `<primitive>`: R3F assigns it onto the instance, shadowing its real `dispose()`
  (crossfade unmounts then crash with "dispose is not a function"). Primitives are never auto-disposed anyway.
- Where a prop and an actor must meet (straws to mouths, dots over a bucket), share the anchor points as constants
  in `story.ts` that both `world.ts` and `cast.ts` import — never duplicate coordinates.
- Effect cards pasted on geometry (a map on a board) need a world-locked yaw: camera billboards visibly float off
  the surface at oblique angles. Free-floating effects stay billboards.
- A long camera glide goes straight: if it would thread geometry, split it with a waypoint key that swings wide.
- The sight-line culler only removes houses sitting in front of sampled camera rays: it can NOT save a glide path that threads the El trestle (never culled), crosses a house row laterally (row is behind the ray starts), or dollies into a column (the S3b end point sat 0.27 m inside an El column and filled the frame with a navy blob). Route crane/glide paths OVER trestles and rows (y above the tallest roof) and still-verify the glide every ~10 f, not just its endpoints.
- For head-on approach choreography (camera and object rushing each other), compute the closest-approach distance and still-verify the frames around it: a front face crossing the 0.2 m near plane winks the whole object out for the rest of the shot (the S8 wave vanished at f1181 and only the frame-QA pop caught it). Retreat the lens instead of pushing in.
- Occlusion checks must cover horizontal structures, not just vertical ones: the v2 S3 witness hid behind the El track bed (a continuous plane) through four placements while every check looked at columns. Trace each hero sightline against decks, beams, rails and roofs explicitly — or keep the lens on the same side as its subject.
- The sight-line culler only guards ±0.6 of the frame: props at the frame edge survive it, so check every sheet for
  edge giants and cut-off blobs.
- faster-whisper CUDA fails at transcribe time (missing `libcublas.so.12`), not at model load: `words.py` retries on
  CPU there too. The setup check transcribes real audio so it proves the working path, not just the import.
- QA "pops" flag planned impacts as well as glitches: account every one against the shot plan (kick, burst, hard cut,
  fast glide) before touching anything.
- Fit the voice to the picture beats (a line must clear its flash/cut) by iterating `--speed`/`--lead`/`--gap` and
  re-reading `lines.json`, not by editing audio. Punctuation-only tokens (em-dashes) drop from `words.json`: harmless.
- Caption pages pop whole strips of pixels at once: in low-motion shots the QA pop detector flags them. Fold every
  page-start frame (±1) into `shots.json` "planned" so the gate only fires on real picture glitches.
- When a placed actor seems missing from a still, check caption-strip occlusion FIRST (bottom-centre placements hide behind the text) before re-deriving positions: v2 molasses chased an "invisible" witness through three placements when he was behind the caption all along. A quick NDC projection script beats mental arithmetic for framing questions.
- The token cap alone does NOT stop orphans (window boundaries strand "A"/"AND" at page ends): run the orphan cascade
  (trailing glue moves to the next page; sentence-final glue and sub-300 ms remnants stay) plus manual splits for audit
  failures, and gate on `scripts/caption_audit.py` (every page ≤2 lines by real-woff2 advances + stroke bleed, zero
  orphans) before the final render.
- An active-word scale-up eats its neighbours' gaps (transform overflow + stroke bleed); size the gap from measured
  worst-case pixels or keep the highlight colour-only. Trim token text: flex boxes drop leading spaces silently.
- Pixel-sized post parameters must scale with resolution: stills are at 0.5, the final at 1.333. R3F clamps dpr to ≥ 1, so `--scale 0.5` stills still render a 1080x1920 buffer.
- **Disk:** every Remotion bundle copies `public/` (~1.3 GB) into `the temp folder\remotion-webpack-bundle-*` and never deletes it. 60+ GB filled the system drive during the bridge passes and a render died with ENOSPC. Always render with `export TEMP='<big drive>/remotion-tmp' TMP='<big drive>/remotion-tmp'` (bridge-stills.mjs sets it itself) and ask the user before deleting old bundle folders in the shared the temp folder (auto mode blocks the sweep). <big drive>/remotion-tmp fills too (~500 folders / 110 GB after the 4 bridge rounds): when a project is finished and nothing is rendering, delete its `remotion-webpack-bundle-*` and `puppeteer_dev_chrome_profile-*` folders there.
- In JS strings write `"<big drive>/remotion-tmp"`, never `"<big drive>\remotion-tmp"` (`\r` becomes a carriage return).
- Remotion writes a silent audio track: mux with `-map 0:v:0 -map 1:a:0`.
- Sub-agents can't write report files in this harness: ask them for a ≤150-word final message and save it yourself to `out/<name>/<n>/REPORT.md`.
- Scratch `.ts` files inside `out/` break `tsc`: name them `.txt`.
- 2K renders run ~4 fps (≈10 min for 67 s). Stills at 0.5 take 3-8 s each after a ~40 s bundle.
- Film grain at 2.5 % made the 2K file 910 MB instead of ~250 MB and will turn to mush on YouTube; the reference has none. Keep it off.
- Shot-specific furniture must hide outside its shots (per-shot visibility groups): a static payout table reads as a random table in every wide it wanders into. Every visible prop must earn its frame.
- Ground/apron quads: stagger depths (street 0.012, aprons 0.02+): coplanar overlaps z-fight into color flicker.
- Every fx card must be tied to a timed event (word/beat): a continuous twinkle reads as random floating junk.
- Symmetric-looking props have a front: verify facing (eyes/hood marks toward the lens) in a still, never by coordinates. Hand-computed screen positions are sign-error-prone: verify all framing empirically, always.
- A character closer than ~6 m to the lens gets decapitated by the caption strip and reads as a mystery brown blob (the S6 "dome" was a watcher's hair with face and torso hidden): keep background cast 8+ m from the lens path, and suspect a too-close actor first whenever a still grows an unplaceable blob.
- Props parented to a mesh must protrude past its surface, and effect cards must sit in open air: the wave debris shipped buried inside the extrusion (invisible 3 rounds), the S9 dust shipped inside the ruined house (depth-hidden). Place burst/dust cards OUTSIDE the geometry toward open space (offsets along the face normal, verified against the wall radius), never at the object centre.
- Verify every fx with bracketed stills (3+ frames across its life), never one frame: a lone still once showed a firing dust trigger as missing (a one-off GPU flake), and fxBurst/fxRing keep full ink past u = 0.5, so a single sample proves nothing either way.
- Animated emergence through containers: grow-then-rise (scale in before moving) so heads never cross walls/lids; verify the contact frames.
- An SFX cue exists only once measured: after mixing, check each SFX family's band energy in its windows vs control windows (a -26 LU hiss hid ~20 dB under the ambience until measured). Hisses sit ~-7.5 LU: above the music, below the narration.
- Any cue/level/generator change invalidates the cached SFX stem: delete `_cache/<name>_sfx.npy` and re-render (a stale cache once shipped old audio; a wrong-path `rm` silently did nothing).
- Chatterbox Turbo exaggeration defaults to 0.0 (flat delivery); the locked 0.6 does real work. Turbo without a reference clip gives an arbitrary (female) voice: always clone.
- Out-of-frame objects cast in-frame shadows: check shadow casters outside close-ups (a flag pole shadowed the chest).
- Dead cartoon reads: X eyes + lolling tongue + grey body. Oversize the X (6 cm reads at 3 m, 3 cm doesn't).
- Chatterbox adapter: per-line wavs + `narration.wav` + `lines.json` + `script.json` in `voice_work/` so `words.py` runs unchanged; pron fixes re-render single lines.
- Record every bug found in verification in this list the same turn (cause + fix): the next video must avoid it from the start.

## Readability traps the verifier caught (check every new prop/shot for these)
- **A swing drawn as one rope that disappears behind the kid reads as a HANGING.** Always two ropes to a wide plank
  with the kid between them (`swingKid` in toon.ts), and a frame whose legs clear the arc (A-frame at each end).
- Props or flotsam closer than ~2 m to a lens become huge cut-off blobs at the frame edge. When a camera moves, re-check
  every prop near its new position (the river cameras moved into the floating hats).
- A foreground bush cut by the frame edge reads as a "green ball"; a foreground prop must be recognisable or gone.
- Flags: red + yellow star/diamond reads as Vietnam's. Use a period-correct flag (St George's cross for England 1831).
- Painted signs lit by a side sun go grey-blue and unreadable: give the sign face an unlit material.
- Golden rim light done as an offset outer copy turns every hat into a picture frame: inner rim only, head/torso only.
- Balcony/railing rails at chest height through characters: put the lens ~2.5 m up so rails cross legs, not torsos.
- Flat holds read as freezes in QA (frozen span ≥12 f): every hold needs a creeping push-in.
