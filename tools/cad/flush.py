exec(open("work/pipeline244.py").read().split("s=rd(sys.argv[1]); ex=TopExp_Explorer")[0])
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakePrism
from OCP.BRepAlgoAPI import BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCP.gp import gp_Ax2, gp_Dir, gp_Vec
import math
def prism_poly(pts,z0,z1):
    pg=BRepBuilderAPI_MakePolygon()
    for x,y in pts: pg.Add(gp_Pnt(x,y,z0))
    pg.Close(); f=BRepBuilderAPI_MakeFace(pg.Wire(),True).Face(); return BRepPrimAPI_MakePrism(f,gp_Vec(0,0,z1-z0)).Shape()
def flush_tool(sgn,z0,z1,protect):
    cy=-267.80; R=17.52; r=4.0; xp=12.70
    ox=xp+r; oy=cy-math.sqrt((R+r)**2-ox**2); P1=(xp,oy); k=R/(R+r); P2=(ox*k,cy+(oy-cy)*k); C=(xp,cy-math.sqrt(R*R-xp*xp))
    S=lambda p:(sgn*p[0],p[1])
    box=prism_poly([S((xp,-305.2)),S((14.6,-305.2)),S((14.6,-278.0)),S((xp,-278.0))],z0,z1)
    ring=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,cy,z0-1),gp_Dir(0,0,1)),R,z1-z0+2).Shape()
    poly=prism_poly([S(P1),S(C),S(P2)],z0-1,z1+1)
    tri=prism_poly([S(P1),S((ox,oy)),S(P2)],z0-1,z1+1)
    fil=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(sgn*ox,oy,z0-2),gp_Dir(0,0,1)),r,z1-z0+4).Shape()
    keep=BRepAlgoAPI_Fuse(BRepAlgoAPI_Fuse(ring,poly).Shape(),BRepAlgoAPI_Cut(tri,fil).Shape()).Shape()
    T=BRepAlgoAPI_Cut(box,keep).Shape()
    for pb in protect: T=BRepAlgoAPI_Cut(T,pb).Shape()
    print("flush tool side",sgn,"vol %.2f valid %s"%(vol(T),V(T)),"fillet O(%.3f,%.3f) P1 y %.3f P2(%.3f,%.3f)"%(sgn*ox,oy,oy,sgn*P2[0],P2[1]))
    return T
# 1) solid from fixed shell (no bulging fill), slot, P259/P256 (no P596 carve)
s=rd("work/p244_k2.brep"); ex=TopExp_Explorer(s,TopAbs_SHELL); sh=TopoDS.Shell_s(ex.Current())
fs=ShapeFix_Shell(sh); fs.Perform(); sh=fs.Shell()
so=BRepBuilderAPI_MakeSolid(sh).Solid(); f=ShapeFix_Solid(so); f.Perform(); so=tryfix(f.Solid()); print("solid",V(so),flush=True)
so=tryfix(cut(so,[rd("work/slot_tool.brep")],0.005)); print("slot",V(so),flush=True)
for n in ["P259","P256"]: so=tryfix(cut(so,[rd(f"work/cur_{n}.brep")],0.005)); print(n,V(so),flush=True)
BRepTools.Write_s(so,"work/p244_m0.brep")
# 2) flush sides
right=flush_tool(+1,254.0,303.5,[BRepPrimAPI_MakeBox(gp_Pnt(12.5,-304.5,297.4),gp_Pnt(23,-292.4,330)).Shape()])
left=flush_tool(-1,254.0,313.0,[BRepPrimAPI_MakeBox(gp_Pnt(-23,-296.0,297.0),gp_Pnt(-12.5,-281.0,330)).Shape()])
BRepTools.Write_s(right,"work/flush_R.brep"); BRepTools.Write_s(left,"work/flush_L.brep")
v0=vol(so)
for fz in [0.0,0.001,0.005]:
    t=cut(so,[right,left],fz)
    if t is not None and not V(t): sf=ShapeFix_Shape(t); sf.Perform(); t=sf.Shape()
    if t is not None and V(t): print("flush fz",fz,"removed %.2f"%(v0-vol(t)),flush=True); so=t; break
else: print("flush FAILED")
BRepTools.Write_s(so,"work/p244_m1.brep")
