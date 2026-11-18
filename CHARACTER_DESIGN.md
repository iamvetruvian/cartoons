# CHARACTER_DESIGN.md — distinct people, not palette swaps

Load this file when creating or changing any character. `Outfit` color swaps on
the fixed skeleton are the floor, not the design. Every named character needs a
brief and must pass the silhouette gate before it appears in a scene.

## Character Brief schema (one per character, file: `characters/<name>.md`)

```md
# <Name> — <role in one line>
shape_language: <round / angular / lanky / squat — and what it says about them>
silhouette: <what makes the outline unique at 64 px: hat, coat, prop, posture>
signature_prop: <the one object that is always with them>
distinguishing_features:
  1. <visible at 3 m>
  2. <visible at 3 m>
  3. <visible at 3 m>
posture_or_gait: <how they stand, walk, or fidget — readable with no face>
face_baseline: <resting preset blend, e.g. 80% stern + 20% neutral>
voice_in_face: <the 2-3 expressions only this character makes>
```

Rules:

- The three distinguishing features must be visible at 3 m in a still — not
  button colors, not belt shades. Hat shape, coat shape, hair mass, prop,
  moustache, a sling, a limp.
- No two characters share a silhouette AND a palette. Change the shape first;
  color is never the only difference.
- Crowd variants need a 3-line mini-brief each (silhouette note + gait note),
  not a full file. Six identical marchers with different jacket hexes is a
  rejected crowd.

## Design ladder (cheapest distinct change first)

1. Hat / hair mass (biggest silhouette lever on a bean head).
2. Coat shape: length, flare, shoulders (dress blob vs torso blob vs stout).
3. Signature prop: rifle, hammer, satchel, crutch, bucket, flag.
4. Posture: lean, head tilt baseline, arm baseline (crossed vs hang).
5. Gait: stride length, bob amplitude, foot pitch.
6. Face baseline: resting preset blend + one asymmetric tic.
7. Palette (last, never first).

## Turnaround + expression sheet (required artifact)

For every named character, render before first use:

1. Turnaround: front, 3/4 (mirror), side, back at 256 px, neutral pose.
2. Expression sheet: 6 faces (neutral, joy, anger, fear, sorrow, signature),
   128 px each, from the parametric presets — this doubles as the texture
   warm-up for the canvas pool.

Render with the real `toon.ts` drawing code (a tiny Node script with
`node-canvas`, or stills of a lineup stage), not a sketch. The sheet is what
the verifier approves.

## Silhouette gate (machine check)

```bash
python scripts/silhouette_check.py out/<name>/silhouettes/*.png
```

Fill every turnaround solid black, normalize to the same height, center, and
compare pairwise: max Intersection-over-Union must be below 0.85. Any pair
above that is the same blob in two costumes — redesign the shape, not the
colors. Then eyeball the black sheet: name every character from silhouette
alone. If you cannot, the audience cannot either.

Gate: `silhouette_check.py` PASS + verifier names the silhouettes correctly.
No pass, no scenes with that character.
