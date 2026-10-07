exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.STEPControl import STEPControl_Writer, STEPControl_Reader, STEPControl_AsIs
S=rd("work/p223_solid.brep"); ex=TopExp_Explorer(S,TopAbs_SOLID); best=None
while ex.More():
    s=ex.Current(); best=s if best is None or vol(s)>vol(best) else best; ex.Next()
from OCP.BRepCheck import BRepCheck_Analyzer
print("main solid vol %.1f valid %s faces %d"%(vol(best),BRepCheck_Analyzer(best).IsValid(),count(best,TopAbs_FACE)))
BRepTools.Write_s(best,"work/p223_final.brep")
w=STEPControl_Writer(); w.Transfer(best,STEPControl_AsIs); w.Write("work/p223_final.step")
r=STEPControl_Reader(); r.ReadFile("work/p223_final.step"); r.TransferRoots(); R=r.OneShape()
print("roundtrip vol %.1f solids %d"%(vol(R),count(R,TopAbs_SOLID)))
