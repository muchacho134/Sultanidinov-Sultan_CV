exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Ax2, gp_Pnt, gp_Dir
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder
s=rd("work/p223_ckpt10.brep"); keep=[]; rm=0; ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); x=b.Get()
    hit=x[0]>-2.05 and x[3]<2.05 and x[2]>217.08 and x[5]<221.18 and x[1]<-236.5 and x[4]<-228.6
    if hit: rm+=1
    else: keep.append(f)
    ex.Next()
print("removed",rm)
c=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0.0024,-236.0,219.12905),gp_Dir(0,1,0)),2.0,236.0-228.7).Shape()
new=[]; ex=TopExp_Explorer(c,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f)
    if a.GetType()==GeomAbs_Cylinder: new.append(f)
    elif a.GetType()==GeomAbs_Plane and a.Plane().Location().Y()<-235.9: new.append(f)
    ex.Next()
sw=BRepBuilderAPI_Sewing(3e-3)
for f in keep+new: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,"work/p223_ckpt11.brep")
print("loops",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),"faces",count(sh,TopAbs_FACE))
