import sys
exec(open(sys.argv[1]).read().split("# step 2")[0].replace("rail_path,p266,out=sys.argv[1:4]","rail_path,p266,out=sys.argv[2:5]"))
from OCP.BRepAdaptor import BRepAdaptor_Curve, BRepAdaptor_Surface
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
BRepTools.Write_s(cur,sys.argv[5])
ct={0:'L',1:'C',6:'B'}
for i,w in enumerate(free_wires(cur)):
    b=Bnd_Box(); BRepBndLib.Add_s(w,b); x=[round(v,1) for v in b.Get()]
    ne=TopTools_IndexedMapOfShape(); TopExp.MapShapes_s(w,TopAbs_EDGE,ne)
    fp=BRepBuilderAPI_FindPlane(w,1e-2)
    d=fp.Plane().Axis().Direction() if fp.Found() else None
    print(i,x,"edges",ne.Extent(),"planar" if fp.Found() else "NONPLANAR",(round(d.X(),2),round(d.Y(),2),round(d.Z(),2)) if d else "")
