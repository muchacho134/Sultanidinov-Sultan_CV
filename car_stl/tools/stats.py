import sys, numpy as np, trimesh
m = trimesh.load(sys.argv[1], force='mesh')
print("tris", len(m.faces), "verts", len(m.vertices))
print("watertight", m.is_watertight, "winding consistent", m.is_winding_consistent, "euler", m.euler_number)
print("bodies (connected components)", len(m.split(only_watertight=False)))
b = m.bounds; print("bounds min", b[0].round(4), "max", b[1].round(4)); print("extent", (b[1]-b[0]).round(4))
print("area", round(m.area, 4), "volume", round(m.volume, 6) if m.is_watertight else "n/a")
e = m.edges_unique_length; print("edge length min/median/max", e.min().round(5), np.median(e).round(5), e.max().round(5))
# principal axes
c = m.vertices - m.vertices.mean(0)
w, v = np.linalg.eigh(np.cov(c.T)); print("PCA eigvals", w.round(5)); print("PCA axes\n", v.round(3))
