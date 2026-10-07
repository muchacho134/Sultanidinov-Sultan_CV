exec(open("fix_trio.py").read().split("# ---- P152")[0])
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism
from OCP.gp import gp_Vec
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
s=rd("work/x_P154.brep"); F=faces(s)
side=[f for f in F if BRepAdaptor_Surface(f).GetType()==GeomAbs_Plane and abs(BRepAdaptor_Surface(f).Plane().Location().X()+2.0)<0.01 and abs(BRepAdaptor_Surface(f).Plane().Axis().Direction().X())>0.99]
side=[f for f in F if BRepAdaptor_Surface(f).GetType()==GeomAbs_Plane and abs(area(f)-82.309)<0.01]
b=[ (f, Bnd_Box()) for f in side]
for f,bx in b: BRepBndLib.Add_s(f,bx)
fminus=[f for f,bx in b if bx.Get()[0]<-1.9][0]
P154=BRepPrimAPI_MakePrism(fminus,gp_Vec(4.0,0,0)).Shape(); P154=TopExp_Explorer(P154,TopAbs_SOLID).Current()
report("P154 (side face extruded 4 mm)",P154)
# P154 original faces should lie on the new solid
BRepMesh_IncrementalMesh(s,0.05,False,0.2); w=0
for f in F:
    loc=TopLoc_Location(); tr=BRep_Tool.Triangulation_s(f,loc)
    if tr is None: continue
    for i in range(1,tr.NbNodes()+1,max(1,tr.NbNodes()//30)):
        d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(tr.Node(i).Transformed(loc.Transformation())).Vertex(),P154); d.Perform(); w=max(w,d.Value())
print("P154 original faces -> new solid: max %.4f mm"%w)
P150=rd("work/P150_solid.brep"); P152=rd("work/P152_solid.brep")
for a,bn,A,B in (("P150","P152",P150,P152),("P150","P154",P150,P154),("P152","P154",P152,P154)):
    d=BRepExtrema_DistShapeShape(A,B); d.Perform(); print(f"gap {a}-{bn}: {d.Value():.4f} mm")
BRepTools.Write_s(P154,"work/P154_solid.brep")
