import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter
from OCP.TopTools import TopTools_ListOfShape
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRep import BRep_Tool
s=rd(sys.argv[1]); Z=float(sys.argv[3])
tool=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,0,Z),gp_Dir(0,0,1)),-100,100,-400,-100).Face()
sp=BRepAlgoAPI_Splitter(); a=TopTools_ListOfShape(); a.Append(s); t=TopTools_ListOfShape(); t.Append(tool)
sp.SetArguments(a); sp.SetTools(t); sp.Build(); r=sp.Shape()
keep=[]; ex=TopExp_Explorer(r,TopAbs_FACE); nd=0
while ex.More():
    f=ex.Current(); b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); x=b.Get()
    if (x[2]+x[5])/2>Z: keep.append(f)
    else: nd+=1
    ex.Next()
sw=BRepBuilderAPI_Sewing(1e-4)
for f in keep: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); print("kept",len(keep),"dropped",nd)
# cap: free wires lying in the plane
fb=ShapeAnalysis_FreeBounds(sh,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); caps=[]
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(w,b,False,False); x=b.Get()
    if abs(x[2]-Z)<1e-3 and abs(x[5]-Z)<1e-3: caps.append(w); print("planar loop at cut: x[%.2f,%.2f] y[%.2f,%.2f] edges %d"%(x[0],x[3],x[1],x[4],count(w,TopAbs_EDGE)))
    ex.Next()
BRepTools.Write_s(sh,sys.argv[2])
print("loops total",count(fb.GetClosedWires(),TopAbs_WIRE))
