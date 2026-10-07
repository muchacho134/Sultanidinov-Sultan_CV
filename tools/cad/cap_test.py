import sys, json, collections
from OCP.STEPControl import STEPControl_Reader
from OCP.TopAbs import *
from OCP.TopExp import TopExp_Explorer, TopExp
from OCP.TopoDS import TopoDS
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.ShapeAnalysis import ShapeAnalysis_FreeBounds
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid, BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire
from OCP.BRepBuilderAPI import BRepBuilderAPI_FindPlane
from OCP.ShapeFix import ShapeFix_Shell, ShapeFix_Solid
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import *
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
from OCP.BRepTools import BRepTools
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib

names={GeomAbs_Plane:'plane',GeomAbs_Cylinder:'cyl',GeomAbs_Cone:'cone',GeomAbs_Sphere:'sph',GeomAbs_Torus:'tor',GeomAbs_BSplineSurface:'bspl'}
def wires(s,tol=1e-3):
    fb=ShapeAnalysis_FreeBounds(s,tol)
    ws=[]
    for comp in (fb.GetClosedWires(),fb.GetOpenWires()):
        ex=TopExp_Explorer(comp,TopAbs_WIRE)
        while ex.More(): ws.append(TopoDS.Wire_s(ex.Current())); ex.Next()
    return ws
r=STEPControl_Reader(); r.ReadFile(sys.argv[1]); r.TransferRoots(); sh=r.OneShape()
it=TopExp_Explorer(sh,TopAbs_SHELL,TopAbs_SOLID); shells=[]
while it.More(): shells.append(TopoDS.Shell_s(it.Current())); it.Next()
out=[]
cat=collections.Counter()
for i,s in enumerate(shells):
    ex=TopExp_Explorer(s,TopAbs_FACE); st=collections.Counter(); nf=0
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); nf+=1
        st[names.get(BRepAdaptor_Surface(f).GetType(),'other')]+=1; ex.Next()
    ws=wires(s)
    # try planar caps
    b=BRep_Builder(); sew=BRepBuilderAPI_Sewing(1e-3); sew.Add(s)
    planar=0
    for w in ws:
        fp=BRepBuilderAPI_FindPlane(w)
        if fp.Found():
            mf=BRepBuilderAPI_MakeFace(fp.Plane(),w)
            if mf.IsDone(): sew.Add(mf.Face()); planar+=1
    sew.Perform(); res=sew.SewedShape()
    ex=TopExp_Explorer(res,TopAbs_SHELL); closed=False; vol=None; valid=None
    while ex.More():
        sx=TopoDS.Shell_s(ex.Current())
        if len(wires(sx))==0 and nf>1 or (len(wires(sx))==0):
            ms=BRepBuilderAPI_MakeSolid(sx); so=ms.Solid()
            fx=ShapeFix_Solid(); fx.Init(so); fx.Perform(); so=fx.Solid()
            p=GProp_GProps(); BRepGProp.VolumeProperties_s(so,p)
            vol=p.Mass(); valid=BRepCheck_Analyzer(so).IsValid(); closed=True
        ex.Next()
    bb=Bnd_Box(); BRepBndLib.Add_s(s,bb); x=bb.Get()
    diag=((x[3]-x[0])**2+(x[4]-x[1])**2+(x[5]-x[2])**2)**.5
    kind=("capped_solid" if closed and valid and vol and vol>0 else "capped_but_bad" if closed else "needs_work")
    cat[kind]+=1
    out.append(dict(i=i,faces=nf,surf=dict(st),loops=len(ws),planar_caps=planar,kind=kind,vol=vol,valid=valid,diag=round(diag,2)))
json.dump(out,open(sys.argv[2],'w'))
print(cat)
