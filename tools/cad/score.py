import sys
exec(open("puzzle.py").read().split("print(\"parts\",len(parts))")[0])
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_Transform
from OCP.gp import gp_Trsf, gp_Vec
def flen(s):
    m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m); L=0
    for i in range(1,m.Extent()+1):
        if m.FindFromIndex(i).Size()==1:
            try: L+=GCPnts_AbscissaPoint.Length_s(BRepAdaptor_Curve(TopoDS.Edge_s(m.FindKey(i))))
            except Exception: pass
    return L
tr=gp_Trsf(); tr.SetTranslation(gp_Vec(0,-0.4,0)); parts["P266"]=BRepBuilderAPI_Transform(parts["P266"],tr,True).Shape()
G={
 "rail":"P262 P266 P267 P268","housing":"P592 P596 P597 P598 P261","screw114":"P114 P115 P116 P117 P118 P119 P120 P121 P122 P123 P124 P125 P126 P128 P129 P130 P132 P133 P134 P135 P136 P137 P138 P139 P140 P141 P142 P143",
 "g110":"P110 P216 P217","g163":"P163 P208","g251":"P251 P258",
 "receiver?":"P223 P244 P255 P245 P240 P264 P259","tube200?":"P200 P227 P185 P202 P207 P206 P186 P165",
 "g144?":"P144 P148 P149 P241","g232?":"P232 P233 P236","g160?":"P160 P213","g191?":"P191 P201"}
for nm,ks in G.items():
    ks=ks.split(); before=sum(flen(parts[k]) for k in ks); r={}
    for tol in (0.05,0.5):
        sw=BRepBuilderAPI_Sewing(tol)
        for k in ks: sw.Add(parts[k])
        sw.Perform(); r[tol]=flen(sw.SewedShape())
    print(f"{nm:10s} {len(ks):2d} parts | open {before:7.0f} mm | joined exactly(0.05): {before-r[0.05]:6.0f} mm ({100*(before-r[0.05])/before:4.1f}%) | joined loosely(0.5): {before-r[0.5]:6.0f} mm ({100*(before-r[0.5])/before:4.1f}%)")
