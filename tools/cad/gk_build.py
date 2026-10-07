exec(open("bcg_build.py").read().split("# A) P214")[0])
from OCP.BRepAdaptor import BRepAdaptor_Surface, BRepAdaptor_Curve
from OCP.GeomAbs import *
from OCP.GProp import GProp_GProps
src=rd("work/x_P189.brep")
F=[]; ex=TopExp_Explorer(src,TopAbs_FACE)
while ex.More(): F.append(TopoDS.Face_s(ex.Current())); ex.Next()
left=[f for f in F if BRepAdaptor_Surface(f).GetType()==GeomAbs_Plane and abs(BRepAdaptor_Surface(f).Plane().Axis().Direction().X())>0.99][0]
tail=BRepPrimAPI_MakePrism(left,gp_Vec(10.1,0,0)).Shape(); print("tail prism vol %.1f"%vol(tail))
# slanted rear cut of the tube: fit a plane through points of the tube edge with 150<z<160.2 and y varying
pts=[]
for f in F:
    if BRepAdaptor_Surface(f).GetType()!=GeomAbs_Cylinder: continue
    e2=TopExp_Explorer(f,TopAbs_EDGE)
    while e2.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(e2.Current())); us=np.linspace(c.FirstParameter(),c.LastParameter(),15); P=np.array([[c.Value(u).X(),c.Value(u).Y(),c.Value(u).Z()] for u in us])
        if P[:,2].min()>150 and P[:,2].max()<160.2 and np.ptp(P[:,1])>3: pts+=list(P)
        e2.Next()
pts=np.array(pts); cen=pts.mean(0); u_,s_,vt=np.linalg.svd(pts-cen); nrm=vt[2]
if nrm[2]<0: nrm=-nrm
print("slanted cut: %d pts, plane normal %s, fit residual %.4f mm"%(len(pts),np.round(nrm,4),np.abs((pts-cen)@nrm).max()))
from OCP.gp import gp_Pln
hs=BRepPrimAPI_MakeHalfSpace(BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(*cen),gp_Dir(*nrm)),-100,100,-100,100).Face(),gp_Pnt(0,-243.9,130)).Solid()
tube=common(cyl(0.0,-243.9,7.25,121.87,175.0),hs)
tube=cut(tube,[box(-10,-262,138.1,10,-249.4,139.74),box(-10,-262,139.74,10,-249.1,180)])
GK=fuse([tube,tail]); u=ShapeUpgrade_UnifySameDomain(GK,True,True,True); u.Build(); GK=u.Shape(); chk("gas key",GK)
BRepTools.Write_s(GK,"work/bcg_GK.brep")
# compare with original P189 faces
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
sh=TopExp_Explorer(GK,TopAbs_SHELL).Current(); w=0
for f in F:
    BRepMesh_IncrementalMesh(f,0.05,False,0.2); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
    for i in range(1,t.NbNodes()+1,max(1,t.NbNodes()//25)):
        d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(t.Node(i).Transformed(loc.Transformation())).Vertex(),sh); d.Perform(); w=max(w,d.Value())
print("P189 original faces -> new gas key surface: max %.4f mm"%w)
# rebuild final union
parts=[rd(f"work/bcg_{n}.brep") for n in ("carrier","P214","GAP","BAR","KNOB")]+[GK]
ALL=fuse(parts); u=ShapeUpgrade_UnifySameDomain(ALL,True,True,True); u.Build(); ALL=u.Shape()
so=TopExp_Explorer(ALL,TopAbs_SOLID).Current()
print("FINAL: solids",count(ALL,TopAbs_SOLID),"| shells",count(ALL,TopAbs_SHELL),"| faces",count(ALL,TopAbs_FACE),"| valid",BRepCheck_Analyzer(so).IsValid(),"| volume %.1f"%vol(so))
BRepTools.Write_s(so,"work/bcg_solid.brep")
