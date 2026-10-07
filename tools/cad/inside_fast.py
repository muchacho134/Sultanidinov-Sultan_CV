import sys, numpy as np
exec(open("probe3.py").read().split("for n in sys.argv[2:]:")[0])
from OCP.TopoDS import TopoDS_Shape
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
F=TopoDS_Shape(); BRepTools.Read_s(F,"work/bcg_solid.brep",BRep_Builder())
skip={"P214","P200","P189","P185","P188"}
res=[]
for n,s in P.items():
    if n in skip: continue
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get()
    if not (x[2]>35 and x[5]<215 and x[0]>-16 and x[3]<45 and x[1]>-285 and x[4]<-230): continue
    BRepMesh_IncrementalMesh(s,0.2,False,0.4); pts=[]
    ex=TopExp_Explorer(s,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            for i in range(1,t.NbNodes()+1,max(1,t.NbNodes()//8)): pts.append(t.Node(i).Transformed(loc.Transformation()))
        ex.Next()
    pts=pts[::max(1,len(pts)//60)]
    st=[str(BRepClass3d_SolidClassifier(F,p,0.05).State()).split('_')[-1] for p in pts]
    nin=sum(1 for q in st if q in ("IN","ON")); res.append((n,len(pts),nin))
inside=[n for n,t,i in res if t and i==t]; partial=[(n,i,t) for n,t,i in res if 0<i<t]; outside=[n for n,t,i in res if i==0]
print("FULLY INSIDE (to delete):",len(inside),sorted(inside))
print("PARTLY inside (kept):",[(n,f"{i}/{t}") for n,i,t in partial])
print("outside (kept):",sorted(outside))
open("work/inside_parts.txt","w").write("\n".join(inside))
