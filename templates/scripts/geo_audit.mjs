// Headless geometric audit: floating, passthrough, burial, occlusion, caption cover.
// Usage: node scripts/geo_audit.mjs out/<name>/geo_manifest.json
// The manifest is exported from world.ts during stills (see snippet below) and must
// sample every ~10th frame PLUS every contact-event frame (lid lift, slam, tip).
// Checks per frame:
//   1. foot-to-ground gap above eps (floating / buried)
//   2. actor volumes vs static colliders (passthrough)
//   3. container contents vs bounds (+ rim when lids shut)
//   4. camera ray to each credited face vs all colliders (decks, beams, roofs included)
//   5. projected face boxes vs caption strip and frame edges
//   6. billboard foot anchor vs ground point under the same pixel (perspective offset)
// Exit code 1 on any FAIL. Pixel QA cannot see a head inside a pot wall — this can.
// Exporter sketch (world.ts, runs wherever bridge-stills renders):
//   import { groundY } from "./placement";
//   const v = new THREE.Vector3();
//   const project = (p) => { v.set(...p).project(camera); return [(v.x*0.5+0.5)*1080, (1-(v.y*0.5+0.5))*1920]; };
//   actors.push({ name, pos, box:[0.6,1.7,0.4], feet:[x, y, z], face:[x, y+1.5, z],
//     facePx: [...project(face), 60, 80], ground: groundY(surfaces, x, z),
//     footPx: project(feet), footGroundPx: project([feet[0], ground, feet[2]]) });
// Debug renders for the verifier: render one top-down orthographic frame with
// collider boxes + foot-contact markers drawn on, plus a wide side view. Models
// read overlays far better than they infer penetration from a beauty frame.
import fs from "node:fs";

const manifestPath = process.argv[2] || "out/bridge/geo_manifest.json";
const fail = [], warn = [];
const F = (m) => fail.push(`FAIL ${m}`);
const W = (m) => warn.push(`WARN ${m}`);

let manifest;
try {
  manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
} catch {
  console.log(`FAIL manifest missing: ${manifestPath} (export it from world.ts during stills)`);
  process.exit(1);
}
const eps = { ground: 0.03, facePx: 6, ...(manifest.eps || {}) };
const frames = manifest.frames || [];
if (!frames.length) { console.log("FAIL manifest has no frames"); process.exit(1); }

// coverage: no gap above 15 frames (glides must be verified every ~10 f)
const fnums = frames.map((x) => x.f).sort((a, b) => a - b);
for (let i = 1; i < fnums.length; i++)
  if (fnums[i] - fnums[i - 1] > 15) W(`f${fnums[i - 1]}-f${fnums[i]}: ${fnums[i] - fnums[i - 1]}f gap with no sample — glides need a sample every ~10 f`);

const overlap1D = (a0, a1, b0, b1) => Math.max(a0, b0) < Math.min(a1, b1);
// ray from o along d (normalized) vs AABB [minx..maxz]; returns hit t or Infinity
const rayBox = (o, d, b) => {
  let t0 = 0, t1 = Infinity;
  for (let i = 0; i < 3; i++) {
    const inv = 1 / (d[i] || 1e-9);
    let a = (b[i] - o[i]) * inv, z = (b[i + 3] - o[i]) * inv;
    if (a > z) [a, z] = [z, a];
    t0 = Math.max(t0, a); t1 = Math.min(t1, z);
    if (t0 > t1) return Infinity;
  }
  return t0;
};
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const norm = (a) => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const rectOverlap = (r, c) => r[0] < c.x1 && r[0] + r[2] > c.x0 && r[1] < c.y1 && r[1] + r[3] > c.y0;

for (const fr of frames) {
  const tag = `f${fr.f}`;
  const boxes = [...(fr.colliders || []), ...(fr.containers || []).map((c) => ({ name: c.name, box: c.box }))];
  for (const a of fr.actors || []) {
    // 1. ground contact
    const g = a.ground ?? fr.ground;
    if (g === undefined || g === null) F(`${tag} ${a.name}: no ground reference — export groundY per actor`);
    else {
      const gap = a.feet[1] - g;
      if (gap > eps.ground) F(`${tag} ${a.name}: FLOATING ${(gap).toFixed(3)} m over ground ${g.toFixed(3)}`);
      if (gap < -eps.ground) F(`${tag} ${a.name}: BURIED ${(-gap).toFixed(3)} m under ground ${g.toFixed(3)}`);
    }
    // 2. actor volume vs colliders (actor box: w,h,d with base at pos.y)
    const [w, h, d] = a.box || [0.6, 1.7, 0.4];
    const ab = [a.pos[0] - w / 2, a.pos[1], a.pos[2] - d / 2, a.pos[0] + w / 2, a.pos[1] + h, a.pos[2] + d / 2];
    for (const c of fr.colliders || [])
      if (overlap1D(ab[0], ab[3], c.box[0], c.box[3]) && overlap1D(ab[1], ab[4], c.box[1], c.box[4]) && overlap1D(ab[2], ab[5], c.box[2], c.box[5]))
        F(`${tag} ${a.name}: PASSTHROUGH inside collider '${c.name}' (actor parked in architecture)`);
    // 4. face sightline vs every box (decks, beams, rails, roofs — not just columns)
    if (a.face && fr.camera) {
      const o = fr.camera.pos, dir = norm(sub(a.face, o)), dist = Math.hypot(...sub(a.face, o));
      for (const c of boxes) {
        const t = rayBox(o, dir, c.box);
        if (t < dist - 0.05) F(`${tag} ${a.name}: face hidden behind '${c.name}' (occluder ${(dist - t).toFixed(2)} m in front)`);
      }
    }
    // 5. face box vs caption strip and frame edges
    if (a.facePx && fr.caption && rectOverlap(a.facePx, fr.caption))
      F(`${tag} ${a.name}: face box inside caption strip — check caption occlusion FIRST before re-deriving positions`);
    if (a.facePx && fr.frame) {
      const [cx, cy, cw, ch] = a.facePx;
      if (cx + cw < 0 || cx > fr.frame.w || cy + ch < 0 || cy > fr.frame.h) F(`${tag} ${a.name}: credited face fully out of frame`);
      else if (cx < 0 || cx + cw > fr.frame.w || cy < 0 || cy + ch > fr.frame.h) W(`${tag} ${a.name}: face cut by frame edge`);
      if (cw < 12 || ch < 12) W(`${tag} ${a.name}: face ${Math.round(cw)}x${Math.round(ch)} px — unreadable at final size?`);
    }
    // 6. billboard perspective offset: foot anchor vs ground under the same pixel
    if (a.footPx && a.footGroundPx) {
      const off = Math.hypot(a.footPx[0] - a.footGroundPx[0], a.footPx[1] - a.footGroundPx[1]);
      if (off > eps.facePx) F(`${tag} ${a.name}: billboard foot offset ${off.toFixed(1)} px from its ground point — card floats off its floor`);
    }
  }
  // 3. containers
  for (const c of fr.containers || []) {
    (c.contents || []).forEach((p, i) => {
      const inside = p[0] > c.box[0] && p[0] < c.box[3] && p[1] > c.box[1] && p[1] < c.box[4] && p[2] > c.box[2] && p[2] < c.box[5];
      if (!inside) F(`${tag} container '${c.name}': content #${i} outside bounds (grow/rise must clear rims — verify frame by frame)`);
      if (c.lidsShut && c.rim !== undefined && p[1] > c.rim) F(`${tag} container '${c.name}': content #${i} above rim ${c.rim} while lids shut`);
    });
  }
  // every credited actor visible somewhere is checked across the film, not per frame
}

console.log(`geo_audit: ${frames.length} frames, eps ground=${eps.ground} m facePx=${eps.facePx} px`);
for (const w of warn) console.log(w);
if (fail.length) { for (const f of fail) console.log(f); console.log(`geo_audit: ${fail.length} FAILs — fix placement, re-export, re-run`); process.exit(1); }
console.log("geo_audit: PASS");
