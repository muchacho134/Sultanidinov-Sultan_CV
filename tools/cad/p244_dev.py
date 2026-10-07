exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepTopAdaptor import BRepTopAdaptor_FClass2d
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Tool
from OCP.gp import gp_Pnt2d
from OCP.TopAbs import TopAbs_IN
import numpy as np, sys
S=rd(sys.argv[1]); O=rd("work/g_P244.brep")
ex=TopExp_Explorer(O,TopAbs_FACE); res=[]; i=0
while ex.More():
    f=TopoDS.Face_s(ex.Current()); g=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,g)
    u0,u1,v0,v1=BRepTools.UVBounds_s(f); cl=BRepTopAdaptor_FClass2d(f,1e-6); sf=BRep_Tool.Surface_s(f); pts=[]
    for a in np.linspace(0.1,0.9,5):
        for b in np.linspace(0.1,0.9,5):
            uv=gp_Pnt2d(u0+a*(u1-u0),v0+b*(v1-v0))
            if cl.Perform(uv)==TopAbs_IN: pts.append(sf.Value(uv.X(),uv.Y()))
    dm=[]
    for p in pts[:8]:
        d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),S); d.Perform(); dm.append(d.Value())
    res.append((i,np.median(dm) if dm else -1,g.Mass())); ex.Next(); i+=1
R=np.array(res); A=R[:,2].sum()
for t in (0.01,0.1,0.5,1.6): print(f"within {t}: {R[R[:,1]<=t,2].sum()/A*100:.1f}% area")
for i,d,a in sorted(res,key=lambda r:-r[2]):
    if d>0.1 and a>40: print(f"face {int(i)} dev {d:.2f} area {a:.0f}")
