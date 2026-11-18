// Relational placement: declare what touches what, never hand-type coordinates.
// placeOn(actor, surface) / inside(obj, container) / attach(prop, socket).
// Resting heights resolve by raycast, so "resting y >= surface" holds by
// construction. Sockets are the single shared anchor constants that world.ts
// and cast.ts both import — the old duplicated-coordinates gotcha is retired.
import * as THREE from "three";

export type V3 = [number, number, number];
export const SU_DEFAULT = 0.00216; // metres per toon design unit (cast.ts SU)

export type BuildName = "adult" | "stout" | "kid";
export type SocketName = "mouth" | "handL" | "handR" | "crown" | "hips" | "feet";

/** Socket offsets in metres from the actor origin (feet centre, facing +z).
 *  Approximate to ±3 cm (heads vary by seed); exact lip-contact is still
 *  verified in stills — but the SOCKET is the one shared constant, never two
 *  hand-typed copies. Kid values are the adult rig at 0.72 scale. */
export const SOCKETS: Record<BuildName, Record<SocketName, V3>> = {
  adult: { mouth: [0, 1.34, 0.02], handL: [-0.19, 0.7, 0], handR: [0.19, 0.7, 0], crown: [0, 1.68, 0], hips: [0, 0.73, 0], feet: [0, 0.02, 0] },
  stout: { mouth: [0, 1.32, 0.02], handL: [-0.22, 0.68, 0], handR: [0.22, 0.68, 0], crown: [0, 1.66, 0], hips: [0, 0.71, 0], feet: [0, 0.02, 0] },
  kid: { mouth: [0, 0.96, 0.02], handL: [-0.14, 0.5, 0], handR: [0.14, 0.5, 0], crown: [0, 1.21, 0], hips: [0, 0.53, 0], feet: [0, 0.02, 0] },
};
export const socket = (build: BuildName, name: SocketName): V3 => [...SOCKETS[build][name]] as V3;

/** Design-canvas (600x1000, soles y=975) → actor-local metres. */
export const designToLocal = (x: number, y: number, su = SU_DEFAULT): [number, number] =>
  [(x - 300) * su, (975 - y) * su];

const _rc = new THREE.Raycaster();
const _down = new THREE.Vector3(0, -1, 0);
const _origin = new THREE.Vector3();

/** Highest surface height under (x, z) starting from fromY. Returns null when
 *  nothing is hit (actor would float over the void — fail loudly, never guess). */
export const groundY = (targets: THREE.Object3D[], x: number, z: number, fromY = 50): number | null => {
  _origin.set(x, fromY, z);
  _rc.set(_origin, _down);
  _rc.far = fromY + 100;
  const hits = _rc.intersectObjects(targets, true);
  return hits.length ? hits[0].point.y : null;
};

/** Rest an object on a surface: y = surface + lift. Pass a raycast hit when the
 *  surface moves (decks, water); pass a constant only for static ground. */
export const placeOn = <T extends THREE.Object3D>(obj: T, surfaceY: number, lift = 0): T => {
  obj.position.y = surfaceY + lift;
  return obj;
};

/** Rest on whatever is under (x, z). Throws when the ray hits nothing — a
 *  floating actor must fail the build, not ship. */
export const placeOnWorld = <T extends THREE.Object3D>(obj: T, targets: THREE.Object3D[], x: number, z: number, lift = 0, fromY = 50): T => {
  const g = groundY(targets, x, z, fromY);
  if (g === null) throw new Error(`placeOnWorld: no ground under (${x}, ${z})`);
  obj.position.set(x, g + lift, z);
  return obj;
};

export type Containment = { ok: boolean; violations: string[] };
/** Clamp an object inside a container Box3 (with margin). Returns violations
 *  instead of silently burying the object in a wall. */
export const inside = <T extends THREE.Object3D>(obj: T, box: THREE.Box3, margin = 0.02): Containment => {
  const violations: string[] = [];
  const p = obj.position, min = box.min, max = box.max;
  if (p.x < min.x + margin) { violations.push(`x ${p.x.toFixed(3)} < min ${min.x.toFixed(3)}`); p.x = min.x + margin; }
  if (p.x > max.x - margin) { violations.push(`x ${p.x.toFixed(3)} > max ${max.x.toFixed(3)}`); p.x = max.x - margin; }
  if (p.y < min.y + margin) { violations.push(`y ${p.y.toFixed(3)} < min ${min.y.toFixed(3)}`); p.y = min.y + margin; }
  if (p.y > max.y - margin) { violations.push(`y ${p.y.toFixed(3)} > max ${max.y.toFixed(3)}`); p.y = max.y - margin; }
  if (p.z < min.z + margin) { violations.push(`z ${p.z.toFixed(3)} < min ${min.z.toFixed(3)}`); p.z = min.z + margin; }
  if (p.z > max.z - margin) { violations.push(`z ${p.z.toFixed(3)} > max ${max.z.toFixed(3)}`); p.z = max.z - margin; }
  return { ok: violations.length === 0, violations };
};

/** Parent a prop to an actor socket (straws to mouths, dots over buckets).
 *  The socket offset is the single source of truth — never duplicate it. */
export const attach = <T extends THREE.Object3D>(prop: T, parent: THREE.Object3D, build: BuildName, name: SocketName, extra: V3 = [0, 0, 0]): T => {
  const s = socket(build, name);
  parent.add(prop);
  prop.position.set(s[0] + extra[0], s[1] + extra[1], s[2] + extra[2]);
  return prop;
};

/** Foot lock: snap a planted ankle to the ground when within tolerance, else
 *  report the gap. Planted feet can neither slide nor hover. */
export const footLock = (ankleY: number, ground: number, eps = 0.03): { y: number; gap: number; ok: boolean } => {
  const gap = ankleY - ground;
  if (Math.abs(gap) <= eps) return { y: ground, gap: 0, ok: true };
  return { y: ankleY, gap, ok: false };
};

/** AABB helper for audit colliders: centre + full extents. */
export const actorBox = (x: number, y: number, z: number, w: number, h: number, d: number) =>
  new THREE.Box3(new THREE.Vector3(x - w / 2, y, z - d / 2), new THREE.Vector3(x + w / 2, y + h, z + d / 2));
