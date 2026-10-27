"""Nose and tail of the refined GLB body: voxel fill of (behind the cleaned end face) AND (inside the
body section where the clean middle tube starts), meshed with marching cubes and united with the tube."""
import sys, numpy as np, trimesh, manifold3d as mf
from scipy import ndimage
from scipy.interpolate import RegularGridInterpolator
from skimage import measure
from matplotlib.path import Path
sys.path.insert(0, '.')
import glb_body as gb

L = gb.L
PITCH = 3.0
X_FRONT_JOIN, X_REAR_JOIN = 560.0, 4840.0       # where the voxel ends hand over to the tube
OVERLAP = 30.0

def to_manifold(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))

def from_manifold(M):
    g = M.to_mesh()
    return trimesh.Trimesh(np.asarray(g.vert_properties)[:, :3], np.asarray(g.tri_verts), process=False)

def end_volume(X, R, ZCS, ys, zs, F, front):
    x_join = X_FRONT_JOIN if front else X_REAR_JOIN
    if front:
        xr = np.arange(np.nanmin(F) - PITCH, x_join + OVERLAP, PITCH)
    else:
        xr = np.arange(x_join - OVERLAP, L - np.nanmin(F) + PITCH, PITCH)
    yr = np.arange(-1000, 1000.1, PITCH); zr = np.arange(120, 1260.1, PITCH)
    YY, ZZ = np.meshgrid(yr, zr, indexing='ij')
    pts = np.c_[YY.ravel(), ZZ.ravel()]
    Fi = RegularGridInterpolator((zs, ys), np.nan_to_num(F, nan=1e5), bounds_error=False, fill_value=1e5)
    Fyz = Fi(np.c_[ZZ.ravel(), YY.ravel()]).reshape(YY.shape)        # depth of the end face at (y, z)
    xface = Fyz if front else L - Fyz
    occ = np.zeros((len(xr), len(yr), len(zr)), np.float32)
    cache = {}
    for i, x in enumerate(xr):
        # inside the tube's own section where the tube exists (blends the seam), its join section beyond
        xs = max(x, x_join) if front else min(x, x_join)
        key = round(xs, 1)
        if key not in cache:
            sy, sz = gb.section(X, R, ZCS, xs)
            poly = np.r_[np.c_[sy, sz], np.c_[-sy[::-1], sz[::-1]]]
            inside = Path(poly).contains_points(pts).reshape(YY.shape)
            sdf = (ndimage.distance_transform_edt(inside) - ndimage.distance_transform_edt(~inside)) * PITCH
            cache[key] = sdf.astype(np.float32)
        face_d = (x - xface) if front else (xface - x)          # signed distance-like along X to the end face
        occ[i] = np.minimum(cache[key], np.clip(face_d, -50, 50))
    return xr, yr, zr, occ

def mc_mesh(xr, yr, zr, phi, front):
    vol = np.pad(phi, 1, constant_values=-50.0)
    vtx, faces, _, _ = measure.marching_cubes(vol, 0.0)
    vtx = (vtx - 1) * PITCH + np.array([xr[0], yr[0], zr[0]])
    m = trimesh.Trimesh(vtx, faces[:, ::-1], process=True)
    trimesh.repair.fix_normals(m)
    trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=6)
    return m

def build():
    d = np.load("out/glb_stations.npz")
    X, R, ZCS = d['X'], d['R'], d['ZCS']
    # clean tube between the joins (stations outside are dropped; the join sections stay)
    keep = (X >= X_FRONT_JOIN - 200) & (X <= X_REAR_JOIN + 200)
    tube = gb.body_mesh(X[keep], R[keep], ZCS[keep])
    T = to_manifold(tube)
    cut = mf.Manifold.cube([X_REAR_JOIN - X_FRONT_JOIN, 3000, 3000]).translate([X_FRONT_JOIN, -1500, -500])
    T = T ^ cut                                                    # intersect: keep join..join
    parts = [T]
    for front, key in ((True, 'f'), (False, 'r')):
        xr, yr, zr, occ = end_volume(X, R, ZCS, d['ys' + key], d['zs' + key], d['F' + key], front)
        print("end", "front" if front else "rear", occ.shape, flush=True)
        parts.append(to_manifold(mc_mesh(xr, yr, zr, occ, front)))
    B = parts[0] + parts[1] + parts[2]
    m = from_manifold(B)
    print("body faces", len(m.faces), "watertight", m.is_watertight, "volume m3", round(m.volume / 1e9, 3), "bounds", m.bounds.round(0).tolist())
    return m

if __name__ == "__main__":
    m = build()
    m.export("out/glb_body_clean.stl")
