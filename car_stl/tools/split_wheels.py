"""Split the fused wheels off the wrapped body mesh and give the body real wheel wells.

body = mesh - well cylinder (r_tyre + gap) from the slot wall outwards, so the arch stays
circular down to the body bottom; the CAD wheels (true cylinders) go back in afterwards.
"""
import sys, json, numpy as np, trimesh
P = json.load(open(sys.argv[2]))
GAP = {"front": 12.0, "rear": 8.0}
m = trimesh.load(sys.argv[1], force='mesh')
tools = []
for lab in ("front", "rear"):
    w = P[lab]; rw = w["r"] + GAP[lab]
    for s in (1, -1):
        y0, y1 = sorted((s * w["wall"], s * (w["y_out"] + 300)))
        cyl = trimesh.creation.cylinder(radius=rw, height=y1 - y0, sections=256)
        cyl.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        cyl.apply_translation([w["x"], (y0 + y1) / 2, w["z"]])
        # Tesla-style well: arch cylinder above the axle, straight vertical walls below it
        box = trimesh.creation.box(extents=[2 * rw, y1 - y0, w["z"] + 200])
        box.apply_translation([w["x"], (y0 + y1) / 2, (w["z"] - 200) / 2])
        tools += [cyl, box]
cutter = trimesh.boolean.union(tools, engine="manifold")
body = trimesh.boolean.difference([m, cutter], engine="manifold")
print("body: tris %d  watertight %s  volume %.3f m3 (was %.3f)  bodies %d" %
      (len(body.faces), body.is_watertight, body.volume / 1e9, m.volume / 1e9, len(body.split(only_watertight=False))))
body.export(sys.argv[3])
# CAD wheels as meshes, for the pictures
wheels = []
for lab in ("front", "rear"):
    w = P[lab]
    for s in (1, -1):
        y0, y1 = sorted((s * w["y_in"], s * w["y_out"]))
        c = trimesh.creation.cylinder(radius=w["r"], height=y1 - y0, sections=128)
        c.apply_transform(trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0]))
        c.apply_translation([w["x"], (y0 + y1) / 2, w["z"]])
        wheels.append(c)
trimesh.util.concatenate(wheels).export(sys.argv[4])
