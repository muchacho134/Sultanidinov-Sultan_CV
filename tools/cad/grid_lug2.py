exec(open("work/pipeline244.py").read().split("s=rd(sys.argv[1]); ex=TopExp_Explorer")[0])
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.gp import gp_Ax2, gp_Dir
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return abs(p.Mass())
P=rd("work/cur_P223.brep"); so=rd("work/p244_pre223.brep"); v0=vol(so)
sides=[BRepAlgoAPI_Common(P,BRepPrimAPI_MakeBox(gp_Pnt(x0,-283.0,252),gp_Pnt(x1,-245,300)).Shape()).Shape() for x0,x1 in [(-25,-12.0),(12.0,25)]]
pk=[rd("work/closed_411.brep"),rd("work/closed_421.brep"),rd("work/closed_410.brep")]
best=None
for hw in [12.65]:
  for z0 in [255.5,255.0,254.0]:
    lug=BRepPrimAPI_MakeBox(gp_Pnt(-hw,-283.1,z0),gp_Pnt(hw,-273.69,283.5)).Shape()
    bore=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-267.9,z0),gp_Dir(0,0,1)),12.7,296.63-z0).Shape()
    tool=lug
    for t_ in sides+[bore]: tool=BRepAlgoAPI_Fuse(tool,t_).Shape()
    for fz in [0.0,0.001]:
        t=cut(so,[tool],fz)
        if t is None or not V(t) or v0-vol(t)<5000 or v0-vol(t)>9000: continue
        t2=cut(t,pk,0.0)
        if t2 is None or not V(t2): continue
        nt=0; ex=TopExp_Explorer(t2,TopAbs_FACE)
        while ex.More():
            if area(ex.Current())<0.05: nt+=1
            ex.Next()
        print("hw",hw,"z0",z0,"fz",fz,"removed %.1f"%(v0-vol(t)),"tiny",nt,flush=True)
        if best is None or nt<best[0]: best=(nt,hw,z0,fz); BRepTools.Write_s(t2,"work/p244_h.brep")
        break
print("best",best)
