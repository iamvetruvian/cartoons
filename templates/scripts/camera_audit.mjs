// Camera-path audit: the lens must never thread geometry or swallow subjects.
// Usage: node scripts/camera_audit.mjs out/<name>/camera_manifest.json
// The manifest is exported during stills (sample camAt every ~5th frame PLUS every
// glide endpoint). Checks per sample and per segment to the NEXT sample:
//   1. lens position inside a collider (dolly into a column = navy blob frame)
//   2. lens SEGMENT vs colliders (glide threading a trestle/row — endpoints can pass
//      while the middle crosses steel, so segments are checked, not just points)
//   3. subject near-plane crossing (a face closer than near+radius winks out)
// Coverage gaps above 10 frames warn. Exit code 1 on any FAIL.
// Exporter sketch (runs wherever stills render; camAt/focusAt from story.ts):
//   import { camAt } from "./story";
//   const c = camAt(id, f);
//   samples.push({ f, pos: [...c.pos], look: [...c.look], fov: c.fov,
//     subjects: [{ name: "wave", pos: [x, y, z], radius: 1.5 }] }); // head-on subjects only
// Colliders reuse the geo_audit boxes (decks, beams, trestles, columns, rows, roofs).
import fs from "node:fs";

const manifestPath = process.argv[2] || "out/bridge/camera_manifest.json";
const fail = [], warn = [];
let manifest;
try {
  manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
} catch {
  console.log(`FAIL manifest missing: ${manifestPath} (sample camAt during stills)`);
  process.exit(1);
}
const near = manifest.near ?? 0.2;
const frames = (manifest.frames || []).sort((a, b) => a.f - b.f);
if (!frames.length) { console.log("FAIL manifest has no frames"); process.exit(1); }
const colliders = manifest.colliders || [];

const fnums = frames.map((x) => x.f);
for (let i = 1; i < fnums.length; i++)
  if (fnums[i] - fnums[i - 1] > 10) warn.push(`WARN f${fnums[i - 1]}-f${fnums[i]}: ${fnums[i] - fnums[i - 1]}f gap — sample every ~5 f plus every glide endpoint`);

const inBox = (p, b) => p[0] > b[0] && p[0] < b[3] && p[1] > b[1] && p[1] < b[4] && p[2] > b[2] && p[2] < b[5];
// segment p0->p1 vs AABB: slab test over t in [0,1]; returns hit t or -1
const segBox = (p0, p1, b) => {
  let t0 = 0, t1 = 1;
  for (let i = 0; i < 3; i++) {
    const d = p1[i] - p0[i];
    if (Math.abs(d) < 1e-9) { if (p0[i] < b[i] || p0[i] > b[i + 3]) return -1; continue; }
    let a = (b[i] - p0[i]) / d, z = (b[i + 3] - p0[i]) / d;
    if (a > z) [a, z] = [z, a];
    t0 = Math.max(t0, a); t1 = Math.min(t1, z);
    if (t0 > t1) return -1;
  }
  return t0;
};
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const norm = (a) => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };

frames.forEach((fr, i) => {
  const tag = `f${fr.f}`;
  for (const c of colliders) {
    // 1. endpoint inside geometry
    if (inBox(fr.pos, c.box)) fail.push(`FAIL ${tag}: lens INSIDE '${c.name}' — dolly endpoint in geometry fills the frame`);
    // 2. segment to next sample (skip across shot cuts: teleports aren't glides)
    const nx = frames[i + 1];
    if (nx && !fr.cutAfter && nx.f - fr.f <= 40) {
      const t = segBox(fr.pos, nx.pos, c.box);
      if (t >= 0) fail.push(`FAIL ${tag}-f${nx.f}: glide threads '${c.name}' (${(t * 100).toFixed(0)}% along) — split with a waypoint that swings wide`);
    }
  }
  // 3. head-on subjects vs the near plane (camera-space depth < near + radius)
  if (fr.subjects && fr.look) {
    const fw = norm(sub(fr.look, fr.pos));
    for (const s of fr.subjects) {
      const depth = dot(sub(s.pos, fr.pos), fw);
      if (depth < near + (s.radius ?? 0.5))
        fail.push(`FAIL ${tag}: '${s.name}' at depth ${depth.toFixed(2)} m crosses the near plane (${near} m) — it winks out; retreat the lens`);
    }
  }
});

console.log(`camera_audit: ${frames.length} samples, near=${near} m, ${colliders.length} colliders`);
for (const w of warn) console.log(w);
if (fail.length) { for (const f of fail) console.log(f); console.log(`camera_audit: ${fail.length} FAILs — reroute the path, re-export, re-run`); process.exit(1); }
console.log("camera_audit: PASS");
