"""Trace the recessed openings on the nose face: depth of the surface behind its smooth envelope,
contoured at DEPTH mm; each closed contour is an intake outline (projected onto the surface)."""
import sys, json, numpy as np, trimesh
from scipy.ndimage import gaussian_filter, binary_opening
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
m = trimesh.load(sys.argv[1], force='mesh'); OUT = sys.argv[2]; DEPTH = float(sys.argv[3])
# frontmost surface x(y, z) on a 10 mm grid, from rays shot backwards (+x) from in front of the nose
G = 10.0
ys = np.arange(-1000, 5, G); zs = np.arange(80, 700, G)
YY, ZZ = np.meshgrid(ys, zs, indexing='ij')
orig = np.c_[np.full(YY.size, -2600.0), YY.ravel(), ZZ.ravel()]
loc, ray, _ = m.ray.intersects_location(orig, np.tile([1.0, 0, 0], (len(orig), 1)), multiple_hits=False)
X = np.full(YY.size, np.nan); X[ray] = loc[:, 0]; X = X.reshape(YY.shape)
valid = ~np.isnan(X) & (X < -1700)                        # nose region only
Xf = np.where(valid, X, np.nanmin(X))
env = gaussian_filter(Xf, 7.0)                            # smooth envelope (~70 mm)
env = np.minimum(env, Xf)                                 # envelope never behind the surface
depth = np.where(valid, Xf - env, 0.0)
from scipy.ndimage import binary_erosion
inner = binary_erosion(valid, iterations=8)               # stay ~80 mm away from the nose silhouette
inner[:, (zs > 600)] = False; inner[:, (zs < 130)] = False
mask = binary_opening((depth > DEPTH) & inner, iterations=2)
fig, ax = plt.subplots(1, 2, figsize=(16, 6))
im = ax[0].imshow(np.where(valid, depth, np.nan).T, origin='lower', extent=[ys[0], ys[-1], zs[0], zs[-1]], cmap='magma', vmax=120)
plt.colorbar(im, ax=ax[0], label='mm behind envelope'); ax[0].set_title('nose: depth behind the smooth envelope')
cs = ax[1].contour(YY, ZZ, mask.astype(float), levels=[0.5], colors='r')
ax[1].imshow(np.where(valid, Xf, np.nan).T, origin='lower', extent=[ys[0], ys[-1], zs[0], zs[-1]], cmap='gray')
ax[1].set_title(f'recess outlines (> {DEPTH:.0f} mm deep)')
for a in ax: a.set_aspect('equal')
fig.tight_layout(); fig.savefig(OUT.replace('.json', '.png'), dpi=70)
loops = []
for path in cs.allsegs[0]:
    if len(path) < 12: continue
    yz = np.asarray(path)
    area = 0.5 * abs(np.sum(yz[:-1, 0] * yz[1:, 1] - yz[1:, 0] * yz[:-1, 1]))
    if area < 6000: continue
    # back onto the surface: x from the frontmost-surface grid
    from scipy.interpolate import RegularGridInterpolator
    fx = RegularGridInterpolator((ys, zs), Xf, bounds_error=False, fill_value=None)
    x = fx(yz)
    loops.append(np.c_[x, yz].tolist())
    print("loop: %d pts  area %.0f cm2  y %.0f..%.0f  z %.0f..%.0f" % (len(yz), area / 100, yz[:, 0].min(), yz[:, 0].max(), yz[:, 1].min(), yz[:, 1].max()))
json.dump(loops, open(OUT, "w"))
