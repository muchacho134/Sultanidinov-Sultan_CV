import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
s=rd(sys.argv[1])
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); ok=[]; bad=[]
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(w,b,False,False); x=b.Get(); ne=count(w,TopAbs_EDGE)
    seen=set(); cands=[]
    ex2=TopExp_Explorer(w,TopAbs_EDGE)
    while ex2.More():
        f=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(TopoDS.Edge_s(ex2.Current()))).First()); srf=BRep_Tool.Surface_s(f)
        if id(srf) not in seen: seen.add(id(srf)); cands.append(srf)
        ex2.Next()
    pf0=BRepBuilderAPI_MakeFace(w,True)
    if pf0.IsDone(): cands=[None]+cands
    best=None
    for srf in cands:
        try:
            pf=pf0.Face() if srf is None else BRepBuilderAPI_MakeFace(srf,w,True).Face()
            sf=ShapeFix_Face(pf); sf.Perform(); pf=sf.Face(); a=area(pf)
            if a<=1e-6: continue
            pb=Bnd_Box(); BRepBndLib.AddOptimal_s(pf,pb,False,False); q=pb.Get()
            if any(abs(q[i]-x[i])>1.0 for i in range(6)): continue
            sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s); sw.Add(pf); sw.Perform(); sh=sw.SewedShape()
            # patch must close the loop
            if count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE)>=count(fb.GetClosedWires(),TopAbs_WIRE): continue
            best=(pf,"plane" if srf is None else "neighbour",a); break
        except Exception as e: pass
    tag=f"{ne:3d} edges x[{x[0]:.1f},{x[3]:.1f}] y[{x[1]:.1f},{x[4]:.1f}] z[{x[2]:.1f},{x[5]:.1f}]"
    if best: ok.append(best[0]); print("OK  ",tag,best[1],round(best[2],2))
    else: bad.append(w); print("OPEN",tag)
    ex.Next()
sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s)
for f in ok: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,sys.argv[2])
print("patched",len(ok),"open",len(bad),"| self-int ok:",BRepAlgoAPI_Check(sh,True,True).IsValid(),"| loops left",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE))
