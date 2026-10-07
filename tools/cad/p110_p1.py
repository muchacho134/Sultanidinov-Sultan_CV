exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.TopTools import TopTools_IndexedDataMapOfShapeListOfShape
from OCP.TopExp import TopExp
from OCP.BRep import BRep_Tool
from OCP.ShapeFix import ShapeFix_Face
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder
s=rd("work/x_P110.brep"); P213=rd("work/p213_solid.brep")
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); patches=[]
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); e=TopoDS.Edge_s(TopExp_Explorer(w,TopAbs_EDGE).Current())
    nb=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(e)).First()); a=BRepAdaptor_Surface(nb)
    if a.GetType()==GeomAbs_Cylinder and a.Cylinder().Radius()<2:
        from OCP.Geom import Geom_CylindricalSurface
        from OCP.gp import gp_Ax3, gp_Pnt, gp_Dir
        surf=Geom_CylindricalSurface(gp_Ax3(gp_Pnt(0.005,-267.9,-300),gp_Dir(0,0,1)),8.0)   # the R8 bore the pin holes run into
        f=BRepBuilderAPI_MakeFace(surf,w,True).Face(); a=None
    else:
        f=BRepBuilderAPI_MakeFace(BRep_Tool.Surface_s(nb),w,True).Face()
    sf=ShapeFix_Face(f); sf.Perform(); f=sf.Face()
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); b=Bnd_Box(); BRepBndLib.Add_s(f,b); x=b.Get()
    kind="R8 bore patch" if a is None else ("plane" if a.GetType()==GeomAbs_Plane else str(a.GetType()))
    print("patch on %-14s area %6.2f  z[%.2f,%.2f] y[%.2f,%.2f]"%(kind,p.Mass(),x[2],x[5],x[1],x[4])); patches.append(f); ex.Next()


sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s); sw.Add(patches[1]); sw.Perform(); BRepTools.Write_s(sw.SewedShape(),"work/p110_patch1.brep")
