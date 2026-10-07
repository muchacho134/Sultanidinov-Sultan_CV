import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
s=rd(sys.argv[1]); B=[float(v) for v in sys.argv[3].split(",")]; yp=float(sys.argv[4])
keep=[]; ex=TopExp_Explorer(s,TopAbs_FACE); rm=0
while ex.More():
    b=Bnd_Box(); BRepBndLib.AddOptimal_s(ex.Current(),b,False,False); x=b.Get()
    inside=x[0]>=B[0] and x[3]<=B[3] and x[1]>=B[1] and x[4]<=B[4] and x[2]>=B[2] and x[5]<=B[5]
    if inside: rm+=1
    else: keep.append(ex.Current())
    ex.Next()
sw=BRepBuilderAPI_Sewing(1e-4)
for f in keep: sw.Add(f)
sw.Perform(); s2=sw.SewedShape(); print("removed",rm)
# fill every loop lying inside the box: project onto plane y=yp
fb=ShapeAnalysis_FreeBounds(s2,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); new=[]
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(w,b,False,False); x=b.Get()
    if x[0]>=B[0]-0.5 and x[3]<=B[3]+0.5 and x[2]>=B[2]-0.5 and x[5]<=B[5]+0.5 and x[1]>=B[1]-0.5 and x[4]<=B[4]+0.5:
        wc=TopoDS.Wire_s(BRepBuilderAPI_Copy(w).Shape()); mf=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,yp,0),gp_Dir(0,1,0)),wc,True)
        if mf.IsDone():
            f=mf.Face(); sf=ShapeFix_Face(f); sf.Perform(); f=sf.Face(); new.append(f)
            print("filled loop y[%.2f,%.2f] x[%.2f,%.2f] z[%.2f,%.2f]"%(x[1],x[4],x[0],x[3],x[2],x[5]))
        else: print("could not fill", x)
    ex.Next()
sw=BRepBuilderAPI_Sewing(1e-3); sw.Add(s2)
for f in new: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,sys.argv[2])
mt=0; e=TopExp_Explorer(sh,TopAbs_EDGE)
while e.More(): mt=max(mt,BRep_Tool.Tolerance_s(TopoDS.Edge_s(e.Current()))); e.Next()
print("loops left",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),"maxtol %.4f"%mt)
