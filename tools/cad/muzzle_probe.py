import sys, numpy as np, collections
exec(open("probe114.py").read().split("k114=[k for k")[0].replace("sys.argv[1]","'%s'"%sys.argv[1]))
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepTools import BRepTools
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepCheck import BRepCheck_Analyzer
names=["P221","solid_222","P215","solid_220"]
M={k.replace("조준경 + 짐벌 + 소총","P"):v for k,v in parts.items()}
for n in names:
    s=st.GetShape_s(M[n][1]); BRepTools.Write_s(s,f"work/mz_{n}.brep")
    b=bb(s); fm=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(s,TopAbs_FACE,fm)
    types=collections.Counter(str(BRepAdaptor_Surface(TopoDS.Face_s(fm.FindKey(i))).GetType()).split('.')[-1][8:] for i in range(1,fm.Extent()+1))
    fb=ShapeAnalysis_FreeBounds(s,1e-4); w=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetClosedWires(),TopAbs_WIRE,w); o=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(fb.GetOpenWires(),TopAbs_WIRE,o)
    print(f"{n}: {str(s.ShapeType()).split('.')[-1][7:]} faces {fm.Extent()} {dict(types)} valid {BRepCheck_Analyzer(s).IsValid()} | z {b[2]:.2f}..{b[5]:.2f} | free loops {w.Extent()+o.Extent()}")
    for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
        ex=TopExp_Explorer(comp,TopAbs_WIRE)
        while ex.More():
            wb=Bnd_Box(); BRepBndLib.Add_s(ex.Current(),wb); x=wb.Get()
            ne=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(ex.Current(),TopAbs_EDGE,ne)
            print("    loop: edges %d  x[%.2f..%.2f] y[%.2f..%.2f] z[%.2f..%.2f]"%(ne.Extent(),x[0],x[3],x[1],x[4],x[2],x[5])); ex.Next()
