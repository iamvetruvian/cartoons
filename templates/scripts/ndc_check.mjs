// NDC framing check: independent recomputation of where faces land on screen.
// Usage: node scripts/ndc_check.mjs out/<name>/geo_manifest.json   (same file geo_audit eats)
// geo_audit trusts the exporter's projected pixels; this script re-derives them from
// 3D positions with pinhole math (a second route to the same truth) and adds the
// film-wide rule: every credited actor must be framable in at least one sample.
// Checks per frame: recomputed face box vs caption strip (FAIL), vs frame edges
// (out FAIL / edge WARN), exporter-vs-recompute agreement (WARN on drift). Roll is
// ignored (bridge rolls are <=2.6 deg — sub-tolerance by design). Exit 1 on FAIL.
import fs from "node:fs";

const manifestPath = process.argv[2] || "out/bridge/geo_manifest.json";
const fail = [], warn = [];
let manifest;
try {
  manifest = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
} catch {
  console.log(`FAIL manifest missing: ${manifestPath} (export it during stills, see geo_audit.mjs)`);
  process.exit(1);
}
const frames = manifest.frames || [];
if (!frames.length) { console.log("FAIL manifest has no frames"); process.exit(1); }

const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const norm = (a) => { const l = Math.hypot(...a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
// project 3D point to pixels (three.js convention: fov vertical, up +Y)
const project = (cam, fov, W, H, p) => {
  const fw = norm(sub(cam.look, cam.pos));
  const right = norm(cross(fw, [0, 1, 0]));
  const up2 = cross(right, fw);
  const v = sub(p, cam.pos), z = dot(v, fw);
  if (z <= 0.01) return null; // behind the lens
  const t = Math.tan((fov * Math.PI) / 360), aspect = W / H;
  return [(dot(v, right) / (z * t * aspect) * 0.5 + 0.5) * W, (1 - (dot(v, up2) / (z * t) * 0.5 + 0.5)) * H];
};
const overlap = (x, y, w, h, c) => x < c.x1 && x + w > c.x0 && y < c.y1 && y + h > c.y0;

const seen = new Map(); // name -> frames where framable (in frame + clear of caption)
for (const fr of frames) {
  const tag = `f${fr.f}`, W = fr.frame?.w ?? 1080, H = fr.frame?.h ?? 1920;
  for (const a of fr.actors || []) {
    if (!a.face || !fr.camera) continue;
    const px = project(fr.camera, fr.camera.fov ?? 40, W, H, a.face);
    const [ew = 60, eh = 80] = a.facePx ? [a.facePx[2], a.facePx[3]] : [];
    if (!px) { fail.push(`FAIL ${tag} ${a.name}: face behind the lens`); continue; }
    const [x, y] = [px[0] - ew / 2, px[1] - eh / 2];
    // cross-check vs exporter pixels (tolerates roll + rounding; drift means investigate)
    if (a.facePx) {
      const drift = Math.hypot(a.facePx[0] + a.facePx[2] / 2 - px[0], a.facePx[1] + a.facePx[3] / 2 - px[1]);
      if (drift > 30) warn.push(`WARN ${tag} ${a.name}: exporter/recompute drift ${drift.toFixed(0)} px — check the exporter math`);
    }
    const out = x + ew < 0 || x > W || y + eh < 0 || y > H;
    if (out) { fail.push(`FAIL ${tag} ${a.name}: recomputed face fully out of frame`); continue; }
    if (x < 0 || x + ew > W || y < 0 || y + eh > H) warn.push(`WARN ${tag} ${a.name}: face cut by frame edge`);
    if (fr.caption && overlap(x, y, ew, eh, fr.caption)) {
      fail.push(`FAIL ${tag} ${a.name}: face under the caption strip — check caption occlusion FIRST`);
      continue;
    }
    if (!seen.has(a.name)) seen.set(a.name, []);
    seen.get(a.name).push(fr.f);
  }
}
// film-wide burial rule: credited in ≥1 sample ⇒ framable in ≥1 sample
const credited = new Set(frames.flatMap((fr) => (fr.actors || []).map((a) => a.name)));
for (const n of credited)
  if (!seen.has(n)) fail.push(`FAIL '${n}': credited but framable in ZERO samples — buried, miscaptioned, or never exported`);

console.log(`ndc_check: ${frames.length} frames, ${credited.size} credited actors`);
for (const w of warn) console.log(w);
if (fail.length) { for (const f of fail) console.log(f); console.log(`ndc_check: ${fail.length} FAILs — reframe, re-export, re-run`); process.exit(1); }
console.log(`ndc_check: PASS (${[...seen.keys()].join(", ") || "no faces"} all framable)`);
