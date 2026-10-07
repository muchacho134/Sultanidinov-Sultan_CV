exec(open("rs_build.py").read().split("G={}")[0])
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GeomAbs import GeomAbs_Line
YB,YC=-267.9,-243.9
def zc(y,r,z0,z1,x=0.0): return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y,z0),gp_Dir(0,0,1)),r,z1-z0).Shape()
def zk(y,r0,r1,z0,z1): return BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0,y,z0),gp_Dir(0,0,1)),r0,r1,z1-z0).Shape()
Z0,ZC,ZR,ZE=69.73,69.93,89.73,90.40
ring=fuse([zk(YB,19.8,20.0,Z0,ZC),zc(YB,20.0,ZC,ZR),zk(YB,20.0,19.80,ZR,ZE)])
top=fuse([zk(YC,9.8,10.0,Z0,ZC),zc(YC,10.0,ZC,ZE),box(-10,-262,Z0,10,YC,ZE)])
F=unify(fuse([ring,top])); chk("front raw",F)
# R2.2 concave fillets where the flats x=+-10 meet the ring (edges along z)
fl=BRepFilletAPI_MakeFillet(F); n=0; ex=TopExp_Explorer(F,TopAbs_EDGE)
while ex.More():
    e=TopoDS.Edge_s(ex.Current()); c=BRepAdaptor_Curve(e)
    if c.GetType()==GeomAbs_Line:
        a=c.Value(c.FirstParameter()); b=c.Value(c.LastParameter())
        if abs(abs(a.X())-10)<1e-3 and abs(a.X()-b.X())<1e-6 and abs(a.Y()-b.Y())<1e-6 and a.Y()<-249 and abs(a.Z()-b.Z())>5: fl.Add(2.2,e); n+=1
    ex.Next()
fl.Build(); print("fillet edges",n,"ok",fl.IsDone())
if fl.IsDone(): F=fl.Shape()
# counterbore R17.12 x 5 deep, keeping the web around the channel (R8.84), and the bottom notch
cb=cut(zc(YB,17.12,Z0-1,74.73),[zc(YC,8.84,Z0-2,76)])
notch=box(-2.5,-292,Z0-1,2.5,-284.0,74.73)
F=cut(F,[cb,notch]); chk("front",F)
BRepTools.Write_s(F,"work/front_piece.brep")
B=rd("work/body_solid.brep")
S=unify(fuse([B,F])); chk("receiver",S)
BRepTools.Write_s(S,"work/p223_solid_raw.brep")
