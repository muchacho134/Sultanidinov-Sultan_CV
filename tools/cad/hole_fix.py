exec(open("front_build.py").read().split("Z0,ZC,ZR,ZE")[0])
from OCP.BRepCheck import BRepCheck_Analyzer
S=rd("work/p223_final.brep")
h=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-240.0,219.13),gp_Dir(0,1,0)),2.0,12.0).Shape()
S2=cut(S,[h]); print("cut done")
ex=TopExp_Explorer(S2,TopAbs_SOLID); best=None
while ex.More():
    s=ex.Current(); best=s if best is None or vol(s)>vol(best) else best; ex.Next()
print("main %.1f valid %s faces %d"%(vol(best),BRepCheck_Analyzer(best).IsValid(),count(best,TopAbs_FACE)))
BRepTools.Write_s(best,"work/p223_final2.brep")
