import cadquery as cq, trimesh, numpy as np
b = cq.Shape.importBrep("out/body.brep")
ws = [cq.Shape.importBrep(f"out/wheel_{i}.brep") for i in range(4)]
for tol, ang in ((0.4, 0.1), (0.3, 0.08), (0.6, 0.12), (0.25, 0.06)):
    cq.exporters.export(cq.Workplane().add(b), "out/t.stl", tolerance=tol, angularTolerance=ang)
    m = trimesh.load("out/t.stl"); m.merge_vertices(digits_vertex=3); m.update_faces(m.nondegenerate_faces()); m.remove_unreferenced_vertices()
    print(tol, ang, m.is_watertight, flush=True)
    if m.is_watertight:
        trimesh.repair.fix_normals(m); m.export("out/luxury_saloon_body_mm.stl")
        parts = [m]
        for w in ws:
            cq.exporters.export(cq.Workplane().add(w), "out/w.stl", tolerance=tol, angularTolerance=ang)
            wm = trimesh.load("out/w.stl"); wm.merge_vertices(digits_vertex=3); trimesh.repair.fix_normals(wm); parts.append(wm)
        allm = trimesh.util.concatenate(parts); allm.export("out/luxury_saloon_mm.stl")
        print("all parts watertight", [p.is_watertight for p in parts]); break
