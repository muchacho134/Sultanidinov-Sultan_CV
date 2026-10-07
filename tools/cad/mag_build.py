exec(open("bcg_build.py").read().split("# A) P214")[0])
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane
from OCP.BRepTools import BRepTools as BT
from OCP.gp import gp_Pln
src=rd("work/x_P256.brep")
F=[]; ex=TopExp_Explorer(src,TopAbs_FACE)
while ex.More(): F.append(TopoDS.Face_s(ex.Current())); ex.Next()
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
left=[f for f in F if BRepAdaptor_Surface(f).GetType()==GeomAbs_Plane and abs(area(f)-4365.7)<0.5][0]     # x=-11.25, has the catch window as 2nd wire
ow=BT.OuterWire_s(left)
inner=[]; ex=TopExp_Explorer(left,TopAbs_WIRE)
while ex.More():
    w=TopoDS.Wire_s(ex.Current())
    if not w.IsSame(ow): inner.append(w)
    ex.Next()
side=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(-11.25,0,0),gp_Dir(1,0,0)),ow,True).Face()
main=BRepPrimAPI_MakePrism(side,gp_Vec(22.5,0,0)).Shape(); print("main prism vol %.1f"%vol(main))
Yb=-359.78
def ycyl(x,z,r,y0,y1): return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y0,z),gp_Dir(0,1,0)),r,y1-y0).Shape()
parts=[main,
       box(-9.75,Yb,104.33,9.75,-281.34,105.83), box(-9.75,Yb,163.83,9.75,-282.34,165.33),
       ycyl(-9.75,105.83,1.5,Yb,-280.90), ycyl(9.75,105.83,1.5,Yb,-280.90), ycyl(-9.75,163.83,1.5,Yb,-282.34), ycyl(9.75,163.83,1.5,Yb,-282.34),
       # spine
       box(-5.65,Yb,165.33,5.65,-284.34,167.83), box(-4.15,Yb,165.33,4.15,-284.34,169.33), ycyl(-4.15,167.83,1.5,Yb,-284.34), ycyl(4.15,167.83,1.5,Yb,-284.34)]
body=fuse(parts)
# spine U-slot: width 8 (x +-4), bottom arc R4 centred y=-293.34, from the spine top down to y=-297.34, through the spine (z 165.33..169.4)
slot=fuse([box(-4,-293.34,165.33,4,-280,170), BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-293.34,165.33),gp_Dir(0,0,1)),4.0,5.0).Shape()])
cuts=[slot]
# magazine-catch pocket: the U window on the left side, 2 mm deep
for w in inner:
    wf=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(-11.25,0,0),gp_Dir(1,0,0)),w,True).Face()
    cuts.append(BRepPrimAPI_MakePrism(wf,gp_Vec(2.0,0,0)).Shape())
mag=cut(body,cuts)
u=ShapeUpgrade_UnifySameDomain(mag,True,True,True); u.Build(); mag=u.Shape()
so=TopExp_Explorer(mag,TopAbs_SOLID).Current()
print("MAG: solids",count(mag,TopAbs_SOLID),"| faces",count(mag,TopAbs_FACE),"| valid",BRepCheck_Analyzer(so).IsValid(),"| self-int",sum(1 for _ in BRepAlgoAPI_Check(so,True,True).Result()),"| volume %.1f"%vol(so))
# every original face must lie on the new surface (except the catch-window rim, now a pocket)
sh=TopExp_Explorer(so,TopAbs_SHELL).Current(); worst=[]
for i,f in enumerate(F):
    BRepMesh_IncrementalMesh(f,0.1,False,0.3); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc); w_=0
    for k in range(1,t.NbNodes()+1,max(1,t.NbNodes()//25)):
        d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(t.Node(k).Transformed(loc.Transformation())).Vertex(),sh); d.Perform(); w_=max(w_,d.Value())
    worst.append(round(w_,4))
print("original faces -> new surface, max deviation per face:",worst)
from OCP.STEPControl import STEPControl_Reader
w=STEPControl_Writer(); w.Transfer(so,STEPControl_AsIs); w.Write("work/mag_solid.step")
r=STEPControl_Reader(); r.ReadFile("work/mag_solid.step"); r.TransferRoots(); s2=r.OneShape(); print("STEP round-trip solids:",0 if s2.IsNull() else count(s2,TopAbs_SOLID))
BRepTools.Write_s(so,"work/mag_solid.brep")
