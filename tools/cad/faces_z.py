import sys
exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAdaptor import BRepAdaptor_Surface
s=rd(sys.argv[1]); z0,z1=float(sys.argv[2]),float(sys.argv[3])
ex=TopExp_Explorer(s,TopAbs_FACE); i=0
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); x=b.Get()
    if x[2]>=z0 and x[5]<=z1:
        a=BRepAdaptor_Surface(f); t=str(a.GetType()).split('.')[-1][8:]; extra=""
        if t=="Plane": n=a.Plane().Axis().Direction(); extra="n(%.2f,%.2f,%.2f)"%(n.X(),n.Y(),n.Z())
        if t in("Cylinder",): extra="R%.2f c(%.2f,%.2f)"%(a.Cylinder().Radius(),a.Cylinder().Location().X(),a.Cylinder().Location().Y())
        if t=="Cone": extra="R%.2f semi%.1f"%(a.Cone().RefRadius(),np.degrees(a.Cone().SemiAngle()))
        p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
        print(f"{i:3d} {t:8s} {extra:22s} area {p.Mass():7.2f} x[{x[0]:6.2f},{x[3]:6.2f}] y[{x[1]:7.2f},{x[4]:7.2f}] z[{x[2]:6.2f},{x[5]:6.2f}]")
    i+=1; ex.Next()
