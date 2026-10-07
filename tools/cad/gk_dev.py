exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepAdaptor import BRepAdaptor_Surface
GK=rd("work/bcg_GK.brep"); sh=TopExp_Explorer(GK,TopAbs_SHELL).Current(); src=rd("work/x_P189.brep")
ex=TopExp_Explorer(src,TopAbs_FACE); i=0
while ex.More():
    f=TopoDS.Face_s(ex.Current()); BRepMesh_IncrementalMesh(f,0.05,False,0.2); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc); w=0
    for k in range(1,t.NbNodes()+1,max(1,t.NbNodes()//40)):
        d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(t.Node(k).Transformed(loc.Transformation())).Vertex(),sh); d.Perform(); w=max(w,d.Value())
    p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p)
    print("face %d %-22s area %6.1f  max deviation %.3f mm"%(i,str(BRepAdaptor_Surface(f).GetType()).split('.')[-1][8:],p.Mass(),w)); i+=1; ex.Next()
