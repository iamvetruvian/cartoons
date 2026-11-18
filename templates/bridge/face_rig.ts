// Parametric face + emotion timeline for the cartoon cast (see ACTING.md).
// Standalone (no imports) so toon.ts can `import type` it with zero runtime cycle.
// FaceParams are DELTAS from neutral: blending presets interpolates offsets, and
// `face` left undefined in FrontOpts/SideOpts reproduces legacy output exactly.
export type ExprName = "neutral" | "stern" | "grin" | "laugh" | "whistle" | "nervous" | "shock"
  | "relief" | "relief_open" | "dazed" | "pained" | "smile" | "smile_closed" | "lick";

export type FaceParams = {
  browAngleL: number; browAngleR: number;   // deg, + = inner end down (anger)
  browHeightL: number; browHeightR: number; // u offsets, + = up (surprise)
  lidL: number; lidR: number;               // 0 open .. 1 shut (0.35 ~= legacy "lid" look)
  pupil: number;                            // 0.7 pinned .. 1.4 blown
  lookX: number; lookY: number;             // -1 .. 1
  cornerL: number; cornerR: number;         // -1 frown .. +1 smile, per side
  open: number;                             // 0 shut .. 1 full "O" / laugh
  wide: number;                             // 0 pout .. 1 stretched grin
  cheek: number;                            // 0 flat .. 1 pushed (genuine smile)
};

export type ArmPose = "hang" | "raised" | "point" | "crossed" | "cover";
export type BodyPose = {
  lean: number;      // deg, + forward
  squash: number;    // 0.9..1.1 vertical pulse (1 = none)
  headTilt: number;  // deg, + = tilt toward facing side
  headYaw: number;   // -1 away .. +1 toward viewer (front view: facing shift)
  kneeBend: number;  // 0 straight .. 1 deep crouch (side view)
  armPose: ArmPose;
};

export const NEUTRAL_FACE: FaceParams = {
  browAngleL: 0, browAngleR: 0, browHeightL: 0, browHeightR: 0,
  lidL: 0.35, lidR: 0.35, pupil: 1, lookX: 0, lookY: 0,
  cornerL: 0, cornerR: 0, open: 0, wide: 0, cheek: 0,
};
export const NEUTRAL_BODY: BodyPose = { lean: 0, squash: 1, headTilt: 0, headYaw: 0, kneeBend: 0, armPose: "hang" };

const P = (p: Partial<FaceParams>): FaceParams => ({ ...NEUTRAL_FACE, ...p });
/** Legacy Expr names as blendable presets. Asymmetry lives here too (smirk, pained). */
export const FACE_PRESETS: Record<ExprName, FaceParams> = {
  neutral: P({}),
  stern: P({ browAngleL: 14, browAngleR: 14, browHeightL: -1, browHeightR: -1, cornerL: -0.5, cornerR: -0.5, lidL: 0.45, lidR: 0.45 }),
  grin: P({ cornerL: 0.8, cornerR: 0.8, open: 0.55, wide: 0.7, cheek: 0.7, lidL: 0.5, lidR: 0.5, browHeightL: 1, browHeightR: 1 }),
  laugh: P({ cornerL: 1, cornerR: 1, open: 1, wide: 0.9, cheek: 1, lidL: 0.7, lidR: 0.7 }),
  whistle: P({ open: 0.25, wide: 0, lidL: 0.6, lidR: 0.6, browHeightL: 1, browHeightR: 1 }),
  nervous: P({ browHeightL: 2, browHeightR: 2, browAngleL: -6, browAngleR: -6, cornerL: -0.2, cornerR: -0.2, open: 0.15, lidL: 0.25, lidR: 0.25 }),
  shock: P({ browHeightL: 5, browHeightR: 5, lidL: 0, lidR: 0, open: 1, wide: 0.2, pupil: 1.3 }),
  relief: P({ cornerL: 0.7, cornerR: 0.7, open: 0.3, cheek: 0.8, lidL: 0.55, lidR: 0.55 }),
  relief_open: P({ cornerL: 0.8, cornerR: 0.8, open: 0.6, cheek: 0.8, lidL: 0.55, lidR: 0.55 }),
  dazed: P({ browHeightL: 2, browHeightR: 1, cornerL: -0.2, cornerR: 0.1, open: 0.2, pupil: 0.8, lidL: 0.4, lidR: 0.4 }),
  pained: P({ browAngleL: 10, browAngleR: -8, browHeightL: 1, browHeightR: 3, cornerL: -0.4, cornerR: -0.4, open: 0.4, lidL: 0.5, lidR: 0.3 }),
  smile: P({ cornerL: 0.7, cornerR: 0.2, lidL: 0.35, lidR: 0.35 }), // smirk: asymmetric by design
  smile_closed: P({ cornerL: 0.6, cornerR: 0.6, lidL: 0.55, lidR: 0.55, cheek: 0.5 }),
  lick: P({ cornerL: 0.5, cornerR: 0.5, open: 0.2 }),
};
export const preset = (n: ExprName): FaceParams => ({ ...FACE_PRESETS[n] });

const clamp = (x: number, a: number, b: number) => Math.max(a, Math.min(b, x));
const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
const smooth = (x: number) => { const u = clamp(x, 0, 1); return u * u * (3 - 2 * u); };
const FKEYS = ["browAngleL", "browAngleR", "browHeightL", "browHeightR", "lidL", "lidR", "pupil",
  "lookX", "lookY", "cornerL", "cornerR", "open", "wide", "cheek"] as const;

/** Weighted blend of faces, e.g. 70% nervous + 30% grin for bravado. */
export const blendFaces = (parts: Array<[FaceParams, number]>): FaceParams => {
  const out = { ...NEUTRAL_FACE };
  let wSum = 0;
  for (const [, w] of parts) wSum += w;
  const w0 = wSum || 1;
  for (const k of FKEYS) {
    let v = 0;
    for (const [f, w] of parts) v += f[k] * w;
    out[k] = v / w0;
  }
  return out;
};

/** Coarse quantization so the canvas pool shares drawings across crowds. */
export const quantizeFace = (f: FaceParams): FaceParams => {
  const q = (v: number, s: number) => Math.round(v / s) * s;
  return {
    browAngleL: q(f.browAngleL, 2), browAngleR: q(f.browAngleR, 2),
    browHeightL: q(f.browHeightL, 1), browHeightR: q(f.browHeightR, 1),
    lidL: q(clamp(f.lidL, 0, 1), 0.25), lidR: q(clamp(f.lidR, 0, 1), 0.25),
    pupil: q(clamp(f.pupil, 0.7, 1.4), 0.1),
    lookX: q(clamp(f.lookX, -1, 1), 0.5), lookY: q(clamp(f.lookY, -1, 1), 0.5),
    cornerL: q(clamp(f.cornerL, -1, 1), 0.2), cornerR: q(clamp(f.cornerR, -1, 1), 0.2),
    open: q(clamp(f.open, 0, 1), 0.2), wide: q(clamp(f.wide, 0, 1), 0.2),
    cheek: q(clamp(f.cheek, 0, 1), 0.25),
  };
};

/** Stable pool-key fragment for a (quantized) face. */
export const faceKey = (f: FaceParams): string =>
  FKEYS.map((k) => (Math.round(f[k] * 100) / 100).toString()).join(",");

export type EmotionKey = { t: number; face: FaceParams; body: BodyPose };
export type EmotionTrack = { keys: EmotionKey[]; overshoot?: number }; // overshoot ~0.15 on peaks

const blendBody = (a: BodyPose, b: BodyPose, t: number): BodyPose => ({
  lean: lerp(a.lean, b.lean, t), squash: lerp(a.squash, b.squash, t),
  headTilt: lerp(a.headTilt, b.headTilt, t), headYaw: lerp(a.headYaw, b.headYaw, t),
  kneeBend: lerp(a.kneeBend, b.kneeBend, t), armPose: t < 0.5 ? a.armPose : b.armPose,
});

/** Sample an emotion track at story time t (seconds). Interior keys are peaks:
 *  with overshoot > 0 they exceed the settle value ~15% for ~0.1 s, then relax. */
export const evalTrack = (track: EmotionTrack, t: number): { face: FaceParams; body: BodyPose } => {
  const keys = [...track.keys].sort((a, b) => a.t - b.t);
  if (!keys.length) return { face: { ...NEUTRAL_FACE }, body: { ...NEUTRAL_BODY } };
  if (t <= keys[0].t) return { face: { ...keys[0].face }, body: { ...keys[0].body } };
  const last = keys[keys.length - 1];
  if (t >= last.t) return { face: { ...last.face }, body: { ...last.body } };
  let i = 0;
  while (i + 1 < keys.length && t >= keys[i + 1].t) i++;
  const a = keys[i], b = keys[i + 1], k = smooth((t - a.t) / Math.max(1e-6, b.t - a.t));
  const face = { ...NEUTRAL_FACE };
  for (const fk of FKEYS) face[fk] = lerp(a.face[fk], b.face[fk], k);
  let body = blendBody(a.body, b.body, k);
  const ov = track.overshoot ?? 0;
  if (ov > 0 && i > 0) {
    // just after leaving peak key a: push past b briefly, decaying over ~0.1 s
    const dt = t - a.t, decay = Math.max(0, 1 - dt / 0.1);
    if (decay > 0) {
      for (const fk of FKEYS) face[fk] += (a.face[fk] - b.face[fk]) * ov * decay;
      body = { ...body, squash: body.squash + (a.body.squash - b.body.squash) * ov * decay };
    }
  }
  return { face, body };
};

export type Word = { w: string; s: number; e: number };
/** Syllable bounce for dialogue mouths: openness follows words.json energy.
 *  Cheap cartoon talk — not phonemes. Add to the acting `open` value. */
export const mouthFromWords = (words: Word[], t: number): number => {
  for (const wd of words) {
    if (t >= wd.s && t < wd.e) {
      const letters = wd.w.toLowerCase().replace(/[^a-z]/g, "") || "a";
      const vowels = (letters.match(/[aeiou]/g) || []).length / letters.length;
      const shout = /[A-Z!]{2,}/.test(wd.w) ? 0.15 : 0;
      return clamp(0.35 + 0.25 * Math.sin(2 * Math.PI * 7 * (t - wd.s)) + 0.3 * vowels + shout, 0, 1);
    }
  }
  return 0.08; // resting chatter gap, not a sealed mouth
};
