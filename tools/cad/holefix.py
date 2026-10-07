import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut
from OCP.TopTools import TopTools_ListOfShape
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
s=rd(sys.argv[1]); big=eval(sys.argv[3]); small=eval(sys.argv[4])
def bb(f):
    b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); return b.Get()
F=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More(): F.append(TopoDS.Face_s(ex.Current())); ex.Next()
m=lambda f,B: all(abs(a-b)<0.03 for a,b in zip(bb(f),B))
Fb=[f for f in F if m(f,big)]; Fs=[f for f in F if m(f,small)]; print(len(Fb),len(Fs))
op=BRepAlgoAPI_Cut(); A=TopTools_ListOfShape(); A.Append(Fb[0]); T=TopTools_ListOfShape(); T.Append(Fs[0]); op.SetArguments(A); op.SetTools(T); op.SetFuzzyValue(1e-4); op.Build()
new=[]; e=TopExp_Explorer(op.Shape(),TopAbs_FACE)
while e.More(): new.append(e.Current()); e.Next()
print("big %.2f small %.2f -> %s"%(area(Fb[0]),area(Fs[0]),[round(area(TopoDS.Face_s(x)),2) for x in new]))
sw=BRepBuilderAPI_Sewing(0.003)
for f in F:
    if not f.IsSame(Fb[0]): sw.Add(f)
for f in new: sw.Add(f)
sw.Perform(); BRepTools.Write_s(sw.SewedShape(),sys.argv[2])
