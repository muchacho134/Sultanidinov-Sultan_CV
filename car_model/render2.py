"""Line-shaded renderer (pencil-sketch look) with ortho and perspective cameras."""
import numpy as np, trimesh
from PIL import Image

def look_at(pos, target, up=(0, 0, 1)):
    pos, target, up = (np.array(v, float) for v in (pos, target, up))
    f = target - pos; f /= np.linalg.norm(f)
    r = np.cross(f, up); r /= np.linalg.norm(r)
    u = np.cross(r, f)
    return pos, np.stack([r, u, f])

def render(mesh, pos, target, up=(0, 0, 1), persp=False, size=(900, 500), fit=None, margin=0.04):
    pos, R = look_at(pos, target, up)
    v = (mesh.vertices - pos) @ R.T                     # x right, y up, z = depth
    f = mesh.faces
    if persp:
        keep = (v[f, 2] > 50).all(1); f = f[keep]
        p2 = v[:, :2] / np.maximum(v[:, 2:3], 1e-6)
    else:
        p2 = v[:, :2].copy()
    fitpts = p2[np.unique(f)] if fit is None else (
        ((np.asarray(fit, float) - pos) @ R.T)[:, :2] / (((np.asarray(fit, float) - pos) @ R.T)[:, 2:3] if persp else 1))
    lo, hi = fitpts.min(0), fitpts.max(0)
    W, H = size
    sc = min((W * (1 - 2 * margin)) / (hi[0] - lo[0]), (H * (1 - 2 * margin)) / (hi[1] - lo[1]))
    off = np.array([W, H]) / 2 - (lo + hi) / 2 * sc
    px = p2 * sc + off; px[:, 1] = H - px[:, 1]
    n = np.cross(v[f[:, 1]] - v[f[:, 0]], v[f[:, 2]] - v[f[:, 0]])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    # face the camera
    cen = v[f].mean(1)
    flip = (n * cen).sum(1) > 0
    n[flip] *= -1
    depth = np.full((H, W), np.inf); nbuf = np.zeros((H, W, 3)); fid = np.full((H, W), -1)
    for i, (a, b, c) in enumerate(f):
        tri = px[[a, b, c]]; z = v[[a, b, c], 2]
        x0, y0 = np.floor(tri.min(0)).astype(int); x1, y1 = np.ceil(tri.max(0)).astype(int)
        x0 = max(x0, 0); y0 = max(y0, 0); x1 = min(x1, W - 1); y1 = min(y1, H - 1)
        if x1 < x0 or y1 < y0: continue
        d = (tri[1, 0] - tri[0, 0]) * (tri[2, 1] - tri[0, 1]) - (tri[2, 0] - tri[0, 0]) * (tri[1, 1] - tri[0, 1])
        if abs(d) < 1e-9: continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        w1 = ((xs - tri[0, 0]) * (tri[2, 1] - tri[0, 1]) - (tri[2, 0] - tri[0, 0]) * (ys - tri[0, 1])) / d
        w2 = ((tri[1, 0] - tri[0, 0]) * (ys - tri[0, 1]) - (xs - tri[0, 0]) * (tri[1, 1] - tri[0, 1])) / d
        w0 = 1 - w1 - w2; m = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not m.any(): continue
        zz = w0 * z[0] + w1 * z[1] + w2 * z[2]
        sub = depth[y0:y1 + 1, x0:x1 + 1]
        m &= zz < sub
        sub[m] = zz[m]
        nbuf[y0:y1 + 1, x0:x1 + 1][m] = n[i]
        fid[y0:y1 + 1, x0:x1 + 1][m] = i
    hit = fid >= 0
    # soft studio lighting: key from upper left/front + fill + rim toward the top
    key = np.array([-0.45, 0.65, -0.6]); key /= np.linalg.norm(key)
    fill = np.array([0.6, 0.2, -0.75]); fill /= np.linalg.norm(fill)
    nk = np.clip(nbuf @ key, 0, 1); nf = np.clip(nbuf @ fill, 0, 1)
    spec = np.clip(nbuf @ key, 0, 1) ** 24
    shade = 105 + 95 * nk + 25 * nf + 22 * spec
    img = np.where(hit, shade, 246.0)
    # edges: depth discontinuities (silhouettes) and normal creases
    dz = np.where(hit, depth, np.nan)
    edge = np.zeros_like(hit)
    # silhouettes: hit / background boundary
    edge[:, :-1] |= hit[:, :-1] != hit[:, 1:]
    edge[:-1, :] |= hit[:-1, :] != hit[1:, :]
    # steps: second difference of depth (zero on smooth slopes, large at a step)
    thr = (8.0 * np.nan_to_num(dz, nan=1e9) / 12000.0) if persp else np.full(dz.shape, 6.0)
    for ax in (0, 1):
        d2 = np.abs(np.roll(dz, 1, ax) - 2 * dz + np.roll(dz, -1, ax))
        edge |= np.nan_to_num(d2, nan=0.0) > thr
    # creases: normal change between neighbours
    for ax in (0, 1):
        dot = (nbuf * np.roll(nbuf, 1, ax)).sum(-1)
        edge |= hit & np.roll(hit, 1, ax) & (dot < 0.82)
    thick = edge.copy()                                  # 1 px dilation so lines survive downsampling
    thick[1:] |= edge[:-1]; thick[:, 1:] |= edge[:, :-1]
    img = np.where(thick, np.minimum(img, 60.0), img)
    return Image.fromarray(img.clip(0, 255).astype(np.uint8))

if __name__ == "__main__":
    import sys
    m = trimesh.load(sys.argv[1], force='mesh')
    render(m, (-6500, -11000, 3200), (2680, 0, 700), persp=True).save(sys.argv[2])
