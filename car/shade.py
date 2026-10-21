"""Shaded orthographic + 3/4 renders with a simple z-buffer rasteriser (numpy)."""
import sys, numpy as np
from PIL import Image
from overlay import load, mesh


def rot(yaw, pitch):
    cy, sy, cp, sp = np.cos(yaw), np.sin(yaw), np.cos(pitch), np.sin(pitch)
    Rz = np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
    Rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    return Rx @ Rz


def raster(V, F, C, R, W=900, H=420, pad=20, N=None):
    """R maps world to camera: camera x right, y up, z towards viewer."""
    P = V @ R.T
    lo, hi = P[:, :2].min(0), P[:, :2].max(0)
    sc = min((W - 2 * pad) / (hi[0] - lo[0]), (H - 2 * pad) / (hi[1] - lo[1]))
    X = (P[:, 0] - lo[0]) * sc + pad + (W - 2 * pad - (hi[0] - lo[0]) * sc) / 2
    Y = H - ((P[:, 1] - lo[1]) * sc + pad + (H - 2 * pad - (hi[1] - lo[1]) * sc) / 2)
    Zc = P[:, 2]
    img = np.ones((H, W, 3)) * 0.97; zb = np.full((H, W), -1e18)
    T = V[F]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    n /= (np.linalg.norm(n, axis=1)[:, None] + 1e-12)
    ncam = n @ R.T
    L = np.array([-0.35, 0.55, 0.75]); L /= np.linalg.norm(L)
    H2 = (L + np.array([0, 0, 1])); H2 /= np.linalg.norm(H2)
    diff = np.clip(ncam @ L, 0, 1); spec = np.clip(ncam @ H2, 0, 1) ** 40
    Ncam = None if N is None else N @ R.T
    for k in range(len(F)):
        if ncam[k, 2] <= 0: continue
        i, j, l = F[k]
        xs = np.array([X[i], X[j], X[l]]); ys = np.array([Y[i], Y[j], Y[l]]); zs = np.array([Zc[i], Zc[j], Zc[l]])
        x0, x1 = int(max(xs.min(), 0)), int(min(xs.max() + 1, W - 1)); y0, y1 = int(max(ys.min(), 0)), int(min(ys.max() + 1, H - 1))
        if x1 < x0 or y1 < y0: continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + .5, np.arange(y0, y1 + 1) + .5)
        d = (ys[1] - ys[2]) * (xs[0] - xs[2]) + (xs[2] - xs[1]) * (ys[0] - ys[2])
        if abs(d) < 1e-12: continue
        a = ((ys[1] - ys[2]) * (gx - xs[2]) + (xs[2] - xs[1]) * (gy - ys[2])) / d
        b = ((ys[2] - ys[0]) * (gx - xs[2]) + (xs[0] - xs[2]) * (gy - ys[2])) / d
        c = 1 - a - b
        m = (a >= -1e-6) & (b >= -1e-6) & (c >= -1e-6)
        if not m.any(): continue
        z = a * zs[0] + b * zs[1] + c * zs[2]
        sub = zb[y0:y1 + 1, x0:x1 + 1]
        m &= z > sub
        sub[m] = z[m]
        if Ncam is None:
            col = C[k] * (0.28 + 0.62 * diff[k]) + 0.35 * spec[k]
            img[y0:y1 + 1, x0:x1 + 1][m] = np.clip(col, 0, 1)
        else:   # smooth (Phong) shading from interpolated vertex normals
            nn = (a[m, None] * Ncam[i] + b[m, None] * Ncam[j] + c[m, None] * Ncam[l])
            nn /= np.linalg.norm(nn, axis=1)[:, None] + 1e-12
            d_ = np.clip(nn @ L, 0, 1); s_ = np.clip(nn @ H2, 0, 1) ** 60
            env = 0.5 + 0.5 * nn[:, 1]          # soft sky/ground gradient
            col = C[k] * (0.22 + 0.55 * d_ + 0.18 * env)[:, None] + 0.45 * s_[:, None]
            img[y0:y1 + 1, x0:x1 + 1][m] = np.clip(col, 0, 1)
    return (img * 255).astype(np.uint8)


def vertex_normals(V, F):
    T = V[F]; n = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    N = np.zeros_like(V)
    for k in range(3):
        np.add.at(N, F[:, k], n)
    return N / (np.linalg.norm(N, axis=1)[:, None] + 1e-12)


def render_sheet(V, F, C, out, N=None, W=1100, H=500):
    views = [rot(0, -np.pi / 2),                     # side (from +y... looking along -y)
             rot(np.pi / 2, -np.pi / 2),             # front
             rot(-np.pi / 2, -np.pi / 2),            # rear
             rot(0, 0),                               # top
             rot(np.radians(35), -np.radians(65)),    # 3/4 front
             rot(np.radians(-150), -np.radians(68))]  # 3/4 rear
    tiles = [raster(V, F, C, R, W, H, N=N) for R in views]
    rows = [np.concatenate(tiles[i:i + 2], 1) for i in range(0, 6, 2)]
    Image.fromarray(np.concatenate(rows, 0)).save(out)


if __name__ == "__main__":
    s = load(sys.argv[1]); V, F = mesh(s, 3.0)
    C = np.tile([0.92, 0.92, 0.94], (len(F), 1))
    render_sheet(V, F, C, sys.argv[2])
