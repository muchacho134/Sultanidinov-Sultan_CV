import sys; sys.path.insert(0, '.')
import cadquery as cq
from cadquery import Vector as V
import car
b = cq.Shape.importBrep("out/body.brep")
stems = [car.box(1665, 1800, 700, 910, 1170, 1225), car.box(1665, 1800, -910, -700, 1170, 1225)]
b = b.fuse(*stems).clean()
solid = b.Solids()[0] if len(b.Solids()) == 1 else b
print("body solids", len(b.Solids()), "valid", b.isValid())
ws = [cq.Shape.importBrep(f"out/wheel_{i}.brep") for i in range(4)]
def asm(scale):
    a = cq.Assembly(name="luxury_saloon")
    sc = lambda s: s.scale(scale) if scale != 1 else s
    a.add(sc(b), name="body", color=cq.Color(0.78, 0.78, 0.80))
    for i, w in enumerate(ws):
        a.add(sc(w), name=f"wheel_{i}", color=cq.Color(0.12, 0.12, 0.12))
    return a
asm(1).save("out/luxury_saloon_mm.step")
asm(0.001).save("out/luxury_saloon_m.step")    # same numeric convention as the DrivAer reference
allc = cq.Compound.makeCompound([b] + ws)
cq.exporters.export(cq.Workplane().add(allc), "out/luxury_saloon_mm.stl", tolerance=0.5, angularTolerance=0.1)
cq.exporters.export(cq.Workplane().add(b), "out/luxury_saloon_body_mm.stl", tolerance=0.5, angularTolerance=0.1)
bb = allc.BoundingBox(); print("bbox", bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax)
