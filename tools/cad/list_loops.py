import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
s=rd(sys.argv[1]); fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); k=0
while ex.More():
    w=ex.Current(); b=Bnd_Box(); BRepBndLib.AddOptimal_s(w,b,False,False); x=b.Get()
    print(f"#{k:2d} {count(w,TopAbs_EDGE):3d} edges x[{x[0]:.1f},{x[3]:.1f}] y[{x[1]:.1f},{x[4]:.1f}] z[{x[2]:.1f},{x[5]:.1f}]  centre ({(x[0]+x[3])/2:.2f},{(x[1]+x[4])/2:.2f},{(x[2]+x[5])/2:.2f})"); k+=1; ex.Next()
