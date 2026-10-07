import sys, numpy as np, collections
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'%s'"%sys.argv[1]))
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepTools import BRepTools
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane, GeomAbs_Cone
M={k.replace("조준경 + 짐벌 + 소총","P"):v for k,v in parts.items()}
for n in ["P159","solid_199","solid_158","P156","solid_153","P152"]:
    s=st.GetShape_s(M[n][1]); BRepTools.Write_s(s,f"work/br_{n}.brep"); b=bb(s)
    fb=ShapeAnalysis_FreeBounds(s,1e-4); w=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,w)
    print(f"{n}: {str(s.ShapeType()).split('.')[-1][7:]} valid {BRepCheck_Analyzer(s).IsValid()} | z {b[2]:.2f}..{b[5]:.2f} | free loops {w.Extent()}")
    ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); fb_=Bnd_Box(); BRepBndLib.Add_s(f,fb_); x=fb_.Get()
        if a.GetType()==GeomAbs_Cylinder: c=a.Cylinder(); d=c.Axis().Direction(); l=c.Location(); info="cyl R=%.3f axis(%.3f,%.3f,%.3f) thru(%.3f,%.3f)"%(c.Radius(),d.X(),d.Y(),d.Z(),l.X(),l.Y())
        elif a.GetType()==GeomAbs_Plane: d=a.Plane().Axis().Direction(); info="plane n(%.2f,%.2f,%.2f)"%(d.X(),d.Y(),d.Z())
        else: info=str(a.GetType()).split('.')[-1][8:]
        print("     ",info,"z[%.2f..%.2f] y[%.2f..%.2f]"%(x[2],x[5],x[1],x[4])); ex.Next()
    for i in range(1,w.Extent()+1):
        wb=Bnd_Box(); BRepBndLib.Add_s(w.FindKey(i),wb); x=wb.Get(); print("      free loop: x[%.2f..%.2f] y[%.2f..%.2f] z[%.2f..%.2f]"%(x[0],x[3],x[1],x[4],x[2],x[5]))
