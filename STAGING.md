# STAGING.md — scene design before scene code

Load this file after the script and voice exist, before writing any `story.ts`.
Do not write camera code, world code, or cast code until every beat has an
approved Scene Brief and the blockout previs stills are approved.

## The one rule

Illustrate the meaning, not the words. A line about peer pressure is staged as
pressure (glances, hesitation, the group moving as one), not as a literal
reading of the nouns. Literalism is the default failure mode; the brief exists
to force a directing choice.

## Scene Brief schema (one per beat, file: `briefs/shot_<id>.md`)

```md
# Shot <id> — <slug>
line: "<exact narration line(s) for this beat>"
subtext: <what the beat is really about in one sentence>
meaning: <the ONE visual proposition this shot makes (a clause, not nouns). If it lists sentence nouns, it is literalism — rewrite it.>
gag_or_metaphor: <the visual idea that carries the meaning>
turn: <what is different between the first and last frame?>
turn_mechanism: <cut | in-shot move> — cuts for any change of place, time, or subject; moves for emphasis inside one continuous moment only
primary_action: <the main story action>
secondary_action: <a different simultaneous action, second subject>
ambient_action: <background life: crowd, weather, animals, props in motion>
foreground: <story-relevant near-layer content, or why empty>
midground: <story-relevant mid-layer content>
background: <story-relevant far-layer content>
absent: <sentence nouns deliberately NOT depicted + why (carried by acting, context, or a prior/later shot)>
entrances: <who/what enters this shot, from where, on what beat — or "none: all residents" with each resident's reason to already be here>
reaction_character: <who reacts with a DIFFERENT emotion than the lead, and why>
camera_why: <why this lens and why this move for this meaning>
emotion_arc_<name>: <anticipation> -> <peak> -> <aftermath>
location_need: <new set or existing set; INT or EXT per the slugline test>
knows: <what the viewer has been shown/told entering this shot (cumulative from prior shots' teaches)>
teaches: <what this shot adds to viewer knowledge (must name every newly introduced entity)>
metaphor: <for explanation beats: tenor | vehicle | sequence plan (cut order). Composites are forbidden — see below.>
story_event: <the keyframed event timed to a word (impact, reveal, entrance...)>
presence: <per credited entity: entered (from/via + frame) | resident (home set) | cut-in (first appearance via this cut)>
```

Rules:

- All three action slots must be filled and must differ from each other.
- All three depth layers must carry something story-relevant, or the brief must
  say why a layer is deliberately empty (and `shot_lint` counts empty layers).
- The reaction character's emotion must differ from the protagonist's, with a
  story reason. Two characters smiling at the same thing is a rejected brief.
- The `turn` must be visible with the sound off. If the first and last frame
  tell the same story, the shot is a postcard, not a scene — restage it.
- Every brief names at least one keyframed story event tied to a word onset
  (reactions land 0–3 frames before the word, per the pipeline).
- Nothing is visible before its cause: every credited entity carries a presence
  tag — `entered` (with from/via + frame), `resident` (only in its home set),
  or `cut-in` (first appearance, established by this cut). Untagged entities,
  residents outside their home set, and any presence before the entity's intro
  shot are rejected briefs (`continuity_lint.py` enforces all three). There is
  no tag for "pre-placed for the camera" — that staging is what this rule
  exists to forbid. Panning to an unmotivated element fails the brief even if
  the geometry is perfect.
- The `absent` slot is mandatory, not decorative: a brief that depicts every
  noun in its sentence is rejected before any option is weighed. Restraint is
  a directing choice and it is graded.
- The `knows` chain must be cumulative: every item in shot N's `teaches`
  appears in shot N+1's `knows`. Stage for what the viewer knows, not for the
  current sentence in isolation.
- The `turn_mechanism` must be `cut` for any change of place, time, or subject
  (`XFADE` counts as a cut). An in-shot move that spans two places, two times,
  or two subjects is a rejected brief — split the setup and cut.
- Explanation beats fill `metaphor` (tenor | vehicle | cut order). Tenor and
  vehicle are always staged as a cut sequence, never composited in one frame —
  no exceptions (see "Metaphors are sequences" below).

## Diverge, then select (mandatory)

For each beat, write THREE different staging ideas (3–5 lines each), then pick
one against this rubric and write a 1-paragraph rationale:

1. Story clarity: does the staging read with the sound off?
2. Visual energy: does something move, change, or escalate inside the shot?
3. Depth use: do foreground, midground, and background all work?
4. Acting opportunity: can faces and bodies carry the subtext?
5. Feasibility: can the engine build it without a new subsystem?

Single-shot ideation is what produces path-of-least-resistance scenes. The
three options and the rationale stay in the brief file; the verifier checks
they exist. One of the three options must be the MINIMAL staging: the fewest
elements that still carry the meaning. If the minimal option wins the rubric
and you still pick a busier one, the rationale must say what each extra
element earns. Density is never its own justification.

## Staging-pattern library (use by name in briefs)

1. **Scale contrast.** A tiny subject against a huge cause (one bolt vs the
   whole span). Use for stakes and absurdity. Grammar: wide that dwarfs, then
   punch-in on the small thing.
2. **Reveal.** Information enters late: a pan, dolly, or foreground wipe that
   uncovers the point on the keyword. Use for twists and consequences.
3. **Cause-and-effect chain.** One action visibly triggers the next across the
   frame (push → swing → higher arc). Use for explanations. Keep the whole
   chain in one shot; never cut mid-chain.
4. **Reaction cutaway.** Cut to the face that the event lands on, 0–3 frames
   before the word. Use whenever the lead's face cannot show the cost.
5. **Anticipation–action–reaction.** Three beats in order: wind-up, impact,
   aftermath face. Impacts without anticipation read as accidents; without
   reaction they read as nothing.
6. **The background is the joke.** The foreground plays it straight while the
   background contradicts it (march on while the deck sags). Use for deadpan.
7. **Follow-through.** After the big motion, something keeps moving (coats,
   dust, water rings, a hat rolling). Every impact shot needs one.
8. **Entrances and exits.** Characters walk into or out of a live frame instead
   of appearing. Use for crowd beats so the world feels continuous.
9. **Contrast cut.** Hard cut between opposites (noise → silence, swagger →
   dread). Use on pivots such as "Luckily / Unluckily".
10. **Escalation ladder.** Same framing, bigger action, three steps (bounce →
    sway → snap). Use for the action beats; the camera stays honest while the
    world gets worse.

## Camera grammar: cuts vs moves (default is CUT)

In-shot moves (push-ins, glides, cranes) are for emphasis inside one
continuous moment: one place, one time, one subject. They are never a
transport mechanism. Any turn that changes place, time, or subject is a
cut (`XFADE` counts as a cut for place/time changes; contrast cuts for
pivots). Consequences:

- A pan, glide, or push that travels to a *different* place, time, or
  subject than it started on is a rejected brief — split the setup and cut.
  This includes the classic failure: the camera pans across a tableau to an
  element the story has not motivated yet. If the lens finds it, the story
  must already have put it there (resident of this set) or brought it there
  on screen (entered) — see presence tags above.
- The `Reveal` pattern (pan/dolly uncovering the point) is for INFORMATION
  (a crack, a tally, a consequence), never for introducing AGENTS: characters
  and crowds the story has not established enter on screen or arrive by cut.
- Match the mechanism to the brief's `turn_mechanism` field exactly; the
  verifier cross-checks them.

## Metaphors are sequences (absolute rule)

An explanation beat has a tenor (the story thing) and a vehicle (the
analogy thing). They live in different worlds and are staged as a CUT
SEQUENCE between those worlds — tenor shot, vehicle shot (an isolated
setup of its own, built like any other set), back if the line needs it.
Never composite tenor and vehicle in one frame: no analogy props sharing
the story set, no "matched motion" composites, no matter how well they
photograph as a still. Composites optimize for the frame; sequences
optimize for sense. `continuity_lint.py` fails any `metaphor.staged`
that is not `"sequence"`.

## One set per shot (no merged places)

A shot has exactly one set. If a beat's elements belong to two story
places (a battle position AND a campfire; a courtroom AND a street), that
is two setups with a cut between them — never one set holding both, and
never per-shot visibility flags smuggling a second place into the first
one's frame. `continuity_lint.py` fails any shot whose residents' homes
span two or more sets. Building the second setup is never a shortcut
violation; merging them always is.

## Continuity ledger (`out/<name>/continuity.json`)

The ledger is the film's world-state: the only artifact that sees across
shots. Seed it from the briefs alongside `shot_manifest.json` (example in
`templates/briefs/`) and keep it current — every added element, moved
prop, or restaged entrance updates the ledger the same turn:

```json
{"sets": {"farm": {"int_ext": "EXT"}},
 "entities": {"farmer-old": {"kind": "lead", "home": "farm",
   "travels": false, "intro_shot": 2, "intro_why": "established on his porch"}},
 "shots": [{"id": 2, "set": "farm",
   "entities": [{"name": "farmer-old", "presence": "resident"}],
   "knows": ["bridge stands"], "teaches": ["farmer-old", "farm prospers"],
   "depicts": ["farmer", "wheat"], "nouns": ["farmer", "wheat", "harvest"]}]}
```

- `sets`: every story place, with INT/EXT. `entities`: `kind`
  (lead/crowd/prop), `home` (a set id, or null ONLY with
  `"travels": true), `intro_shot` + `intro_why` (the story beat that
  motivates them — nothing may appear before it).
- Per shot: one `set`; per entity a presence tag — `entered` (requires
  `via` + `frame`), `resident` (only in its home set; travellers may
  never be resident), `cut-in` (first appearance only, established by
  this cut).
- `knows`/`teaches`: audience knowledge in concept words (lowercase).
  Every `teaches` item must appear in the next shot's `knows`, and every
  newly introduced entity must be named in its shot's `teaches`.
- `depicts`/`nouns`: the shot's depicted elements and the sentence's
  concepts, BOTH in one shared lowercase vocabulary (singular concept
  keys: `emu`, not "emus"/"birds"). Noun coverage
  (|depicts ∩ nouns| / |nouns|) above 0.8 FAILS — the shot depicts
  everything instead of illustrating the meaning. (Extras outside the
  sentence are fine; their motivation is checked via presence/home.
  Sentences under 4 concepts are exempt: depicting a 3-concept situation
  fully — gun, targets, place — is correct staging.)
- Optional `metaphor: {tenor, vehicle, staged}` — `staged` must be
  `"sequence"`.
- `continuity_lint.py` enforces: tags present and valid; residents in
  home sets; no presence before `intro_shot`; no location change without
  `entered` travel (teleports); no merged resident sets; coverage ≤ 0.8;
  sequence-only metaphors; the teaches→knows chain. Usage:
  `python scripts/continuity_lint.py out/<name>/continuity.json`.

## Blockout previs (approve composition before painting)

Render grey-box stills with labelled actors at low resolution and approve
composition before any painted textures, ink, or DOF work.

Procedure:

1. Set `PREVIS=1` when rendering stills:
   `PREVIS=1 BRIDGE_ENTRY=src/index.ts node scripts/bridge-stills.mjs out/<name>/previs/x_ <first,mid,last frames> 0.25`
   (if the env var doesn't reach the browser bundle in your Remotion version, flip the `PREVIS` const in world.ts instead)
2. `world.ts` checks `process.env.PREVIS`: flat grey lambert materials, fog off,
   ink off, DOF off, and a floating text sprite over each actor with its role
   plus its continuity presence tag (`LEAD:entered`, `REACT:resident`,
   `CROWD:cut-in`, prop names + tags). Minimal snippet:

```ts
const PREVIS = process.env.PREVIS === "1";
// in materials: PREVIS ? new THREE.MeshLambertMaterial({ color: "#9aa0aa" }) : lam(...)
// per actor: add a canvas-sprite label at y + 2.4 m, visible only when PREVIS
```

3. Render first, middle, and last frame of every shot, PLUS the neighbor pair
   for every cut (shot N's last frame + shot N+1's first frame side by side).
4. Approval checklist per shot: the `turn` is visible across the three stills;
   three depth layers read; no actor is fully occluded; no credited face is
   under the caption strip; the camera move has a visible reason; every
   presence tag on screen matches `continuity.json` (nobody visible lacks a
   motivation). Neighbor pairs must show entrances reading (nobody pops in),
   nobody vanishing without exiting, and residents already established.
5. Reject freely — previs stills cost seconds. A rejected previs is a saved
   build. Do not start `story.ts` camera code until previs passes.

## Gate

- `briefs/shot_<id>.md` exists for every shot, with three options + rationale.
- Previs stills exist (3 per shot) and are verifier-approved.
- Each brief's `story_event`, entity list, and layer list seed the
  `shot_manifest.json` that `shot_lint.py` checks. If the lint fails later,
  the brief was fiction — fix the scene, not the manifest.
- Each brief's `presence`, `knows`/`teaches`, `depicts`/`nouns`, and
  `metaphor` seed `continuity.json`, and `continuity_lint.py` PASSES before
  any `story.ts` code. Same rule: lint failure means the staging is
  fiction — restage (usually: cut instead of pan, entrance instead of
  pre-placement, sequence instead of composite), never weaken the ledger.

## INT dollhouse staging (user-locked house style)

Open-faced room boxes — floor + back wall + two side walls, no front wall, no
ceiling — with the EXT camera outside looking in (film convention: scene inside
+ camera outside still shoots as exterior coverage). One room per INT location
as a per-shot-visible world.ts group on a separate stage apron away from the
town (never embedded in a house row), so sight-lines, the culler and roofs can
never interfere. Sunlight rakes in through the open face as usual; add a warm
practical only for evening interiors. Camera grammar is unchanged (the lens
never enters the room); INT/EXT changes are always hard cuts. Verify in stills:
open face toward the lens, no roof or ceiling in frame, back wall dressed
(never a bare flat plane).

## Landmines (camera — learned the hard way, machine-checked where possible)

- A long glide goes straight: if it would thread geometry, split it with a
  waypoint key that swings wide (`camera_audit.mjs` fails threaded paths).
- The sight-line culler only removes houses in front of sampled rays: it can
  NOT save a glide through a trestle, across a house row, or into a column
  (route OVER roofs; `camera_audit.mjs` checks endpoints AND segments).
- Head-on approach: compute closest-approach distance — a face crossing the
  0.2 m near plane winks the whole object out (`camera_audit.mjs` near check).
- Occlusion covers horizontal structures too: trace hero sightlines against
  decks, beams, rails and roofs, not just columns (`geo_audit.mjs` §4).
- The culler only guards ±0.6 of the frame: check every sheet for edge giants
  and cut-off blobs (`ndc_check.mjs` flags edge-cut faces).
- Missing actor? Check caption-strip occlusion FIRST before re-deriving
  positions (`ndc_check.mjs` + `geo_audit.mjs` §5 catch it).
- Cast closer than ~6 m gets decapitated by the caption strip into a mystery
  blob: keep background cast 8+ m from the lens path.
- Props/flotsam within ~2 m of a moving lens become huge cut-off blobs;
  re-check every prop near a moved camera. A foreground prop must be
  recognisable or gone (no green balls, no grey mushrooms).
- Rails at chest height through characters: put the lens ~2.5 m up so rails
  cross legs, not torsos.
- Flat holds read as freezes (≥12 f): every hold needs a creeping push-in
  (`shot_lint.py` motion floor + `short_qa.py` frozen spans enforce it).
