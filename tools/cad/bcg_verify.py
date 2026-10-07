import sys
exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.BRepAdaptor import BRepAdaptor_Surface
F=rd("work/bcg_solid.brep"); shell=TopExp_Explorer(F,TopAbs_SHELL).Current()
def faces(sh):
    L=[]; ex=TopExp_Explorer(sh,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
def samples(f,k=12):
    BRepMesh_IncrementalMesh(f,0.1,False,0.3); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc); out=[]
    if t is None: return out
    for i in range(1,t.NbNodes()+1,max(1,t.NbNodes()//k)): out.append(t.Node(i).Transformed(loc.Transformation()))
    return out
def dist(p,target): d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),target); d.Perform(); return d.Value()
def inside(p):
    c=BRepClass3d_SolidClassifier(F,p,1e-4); return str(c.State()).split('.')[-1]
for n in ("P214","P200","P189","P185","P188"):
    s=rd(f"work/x_{n}.brep"); on=0; inn=0; outs=[]
    for i,f in enumerate(faces(s)):
        P=samples(f); 
        if not P: continue
        dm=max(dist(p,shell) for p in P); st=[inside(p) for p in P]
        a=BRepAdaptor_Surface(f); t=str(a.GetType()).split('.')[-1][8:]
        p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
        if dm<0.02: on+=1
        elif all(x in ("TopAbs_IN","TopAbs_ON") for x in st): inn+=1
        else: outs.append((i,t,round(p.Mass(),1),round(dm,2)))
    print(f"{n}: faces on new surface {on}, faces now inside the solid {inn}, faces sticking OUT of the new solid: {outs}")
