import time
exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeThickSolid
from OCP.BRepCheck import BRepCheck_Analyzer
S=rd("work/x_P596.brep")
for off in (-1.5,1.5):
    t=time.time(); m=BRepOffsetAPI_MakeThickSolid(); m.MakeThickSolidBySimple(S,off); 
    try: m.Build(); ok=m.IsDone()
    except Exception as e: print("err",e); continue
    if ok:
        r=m.Shape(); print(off,"done",time.time()-t,"valid",BRepCheck_Analyzer(r).IsValid(),"vol",vol(r),count(r,TopAbs_SOLID),count(r,TopAbs_FACE))
        BRepTools.Write_s(r,f"work/thick_{off}.brep")
    else: print(off,"fail")
