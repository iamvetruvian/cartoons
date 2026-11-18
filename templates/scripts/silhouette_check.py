# Silhouette gate: no two characters may be the same blob in two costumes.
# Usage: python scripts/silhouette_check.py out/<name>/silhouettes/*.png [--threshold 0.85]
# Input: turnaround renders filled solid black on white (any size; alpha is
# flattened). Each pair is normalized to the same height, centered, and scored
# by Intersection-over-Union. Any pair above threshold FAILS.
# Exit code 1 on any FAIL. Gate must pass before the character appears in scenes.
import sys
import numpy as np
from PIL import Image

MAX_IOU = 0.85
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if "--threshold" in sys.argv:
    MAX_IOU = float(sys.argv[sys.argv.index("--threshold") + 1])
if len(args) < 2:
    print("silhouette_check: need >=2 silhouette PNGs")
    sys.exit(1)


def mask(path, h=256):
    im = Image.open(path).convert("RGBA")
    arr = np.array(im).astype(np.float32)
    alpha = arr[..., 3:4] / 255.0
    rgb = arr[..., :3] / 255.0
    flat = rgb * alpha + 1.0 * (1 - alpha)  # composite over white, 0..1
    ink = flat.mean(axis=2) < 0.5  # black fill = character
    ys, xs = np.nonzero(ink)
    if len(xs) == 0:
        return np.zeros((h, h), bool)
    crop = ink[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    scale = h / max(1, crop.shape[0])
    w = max(1, round(crop.shape[1] * scale))
    small = np.array(Image.fromarray(crop).resize((w, h), Image.NEAREST), bool)
    out = np.zeros((h, h), bool)
    x0 = max(0, (h - w) // 2)
    out[:, x0:x0 + min(w, h)] = small[:, :min(w, h)]
    return out


masks = {p: mask(p) for p in args}
fails = []
keys = list(masks)
for i in range(len(keys)):
    for j in range(i + 1, len(keys)):
        a, b = masks[keys[i]], masks[keys[j]]
        inter = np.logical_and(a, b).sum()
        union = np.logical_or(a, b).sum()
        iou = inter / max(1, union)
        print(f"  {keys[i]} vs {keys[j]}: IoU {iou:.3f}")
        if iou >= MAX_IOU:
            fails.append((keys[i], keys[j], iou))
if fails:
    for a, b, iou in fails:
        print(f"FAIL {a} vs {b}: IoU {iou:.3f} >= {MAX_IOU} — same blob, redesign the SHAPE (hat/coat/prop/posture), not colors")
    sys.exit(1)
print(f"silhouette_check: PASS ({len(keys)} characters, max IoU below {MAX_IOU})")
