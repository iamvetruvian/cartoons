# ACTING.md — faces, bodies, and emotion over time

Load this file when writing `cast.ts` roles. Faces are parametric and emotions
are timelines. One static expression per shot is a rejected performance.

## Face model (`templates/bridge/face_rig.ts`)

`FaceParams` — all fields blendable, all sides independent (asymmetry allowed):

```ts
type FaceParams = {
  browAngleL, browAngleR: number;   // deg, + = inner end down (anger)
  browHeightL, browHeightR: number; // u offsets, + = up (surprise)
  lidL, lidR: number;               // 0 open .. 1 shut
  pupil: number;                    // 0.7 pinned .. 1.4 blown
  lookX, lookY: number;             // -1 .. 1
  mouthCornerL, mouthCornerR: number; // -1 frown .. +1 smile, per side
  mouthOpen: number;                // 0 shut .. 1 full "O"/laugh
  mouthWide: number;                // 0 pout .. 1 stretched grin
  cheek: number;                    // 0 flat .. 1 pushed (genuine smile)
};
```

The 14 legacy `Expr` names stay as presets (`FACE_PRESETS`), resolved through
`blendFaces()` so old code keeps working. New acting writes params directly
or blends presets with weights, e.g. 70% `nervous` + 30% `grin` for bravado.

Rules:

- No lead holds one preset for a whole shot. Minimum: anticipation → peak
  (with slight overshoot) → settle, keyed to the word onset minus 0–3 frames.
- Asymmetry is mandatory somewhere in every film: a one-sided smirk, a single
  raised brow, a sidelong look. Symmetric faces read as templates.
- `mouthOpen` on dialogue shots follows the voice: sample `words.json` energy
  per word (`mouthFromWords()`), so talking faces move with the narration
  instead of sitting on a frozen grin. This is syllable bounce, not phonemes —
  cheap and effective at cartoon scale.
- Pupil and lids do the quiet acting: pinned pupils + wide lids = fear;
  slow lid drop = relief; look-away + brow up = guilt.

## Body acting (same keys as the face)

Every emotion key carries a `BodyPose`: `lean` (deg, + forward), `squash`
(0.9–1.1 scale pulse on impacts), `headTilt` (deg), `headYaw` (toward/away),
`armPose` (hang / crossed / raised / pointing / covering), `kneeBend`. The
face never acts alone:

- Shock: lean back 6°, head back, arms up, THEN the face peaks.
- Shame: lean in, head down 10°, look down.
- Pride: chest up (negative squash held 10 f), chin up, look level.
- Laughter: squash pulse 1.06 → 0.96 at 6 Hz for the duration, head rocking.

Implement through the existing `tilt` / `headTilt` plumbing in `toon.ts`; the
`BodyPose` struct just forces the agent to specify all of it per key instead
of leaving the body on `stand` defaults.

## Emotion tracks

```ts
type EmotionKey = { t: number; face: FaceParams; body: BodyPose };
type EmotionTrack = { keys: EmotionKey[]; overshoot?: number };
const v = evalTrack(track, t); // smootherstep between keys, overshoot on peaks
```

- Key times are story seconds, reactions 0–3 frames before the word.
- Cap: ≤6 keys per character per shot. More keys than that is fidgeting.
- Overshoot: peaks exceed the settle value by ~15% for 2–3 frames, then relax.
  Flat-line emotion curves are what template acting looks like in data.

## Texture-cache budget (read before emoting)

`cast.ts` keeps one canvas per distinct drawing. Parametric faces multiply the
cache: quantize every param (`quantizeFace()`: brows to 1°, lids to 0.25,
mouth to 0.2, look to 0.5) and share keys across crowds. Rules:

- Crowd: ≤8 distinct faces per shot (variants share keys by design).
- Leads: ≤12 distinct faces per shot.
- Prerender a 6-expression sheet per lead at build time; the sheet doubles as
  the character-design gate artifact (see `CHARACTER_DESIGN.md`).
- If the pool churns (canvases reallocated mid-shot), coarsen quantization
  before simplifying the acting.
- Machine side: flip `PERF_DUMP` in world.ts, render stills across every shot,
  and run `perf_budget.py` on the log — it gates per-shot live canvases and
  megabytes before the final render.

## Verifier checklist for acting

1. Mute the film: is the emotion arc readable from faces and bodies alone?
2. Scrub each lead shot: does the face change at least twice (anticipation,
   peak, settle)?
3. Freeze any 3 consecutive shots: are the lead faces different?
4. Is there at least one asymmetric expression and one full-body reaction?
5. Do talking mouths move with the words (spot-check 3 dialogue shots)?
