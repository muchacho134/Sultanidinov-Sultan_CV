import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
s=rd(sys.argv[1]); skip=set(int(a) for a in sys.argv[3].split(",")) if len(sys.argv)>3 and sys.argv[3] else set()
m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m)
faces=[]; ex=TopExp_Explorer(s,TopAbs_FACE)
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.Add_s(f,b); faces.append((f,b)); ex.Next()
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
def local_ok(pf):
    b=Bnd_Box(); BRepBndLib.Add_s(pf,b); b.Enlarge(0.3)
    cp=TopoDS_Compound(); B=BRep_Builder(); B.MakeCompound(cp); B.Add(cp,pf)
    for f,fb_ in faces:
        if not b.IsOut(fb_): B.Add(cp,f)
    return BRepAlgoAPI_Check(cp,True,True).IsValid()
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); ok=[]; k=-1; n0=count(fb.GetClosedWires(),TopAbs_WIRE)
while ex.More():
    k+=1; w=TopoDS.Wire_s(ex.Current()); b=Bnd_Box(); BRepBndLib.Add_s(w,b); x=b.Get(); ne=count(w,TopAbs_EDGE)
    tag=f"#{k:2d} {ne:3d} edges x[{x[0]:.1f},{x[3]:.1f}] y[{x[1]:.1f},{x[4]:.1f}] z[{x[2]:.1f},{x[5]:.1f}]"
    if k in skip: print("SKIP",tag); ex.Next(); continue
    seen=set(); cands=[]; ex2=TopExp_Explorer(w,TopAbs_EDGE)
    while ex2.More():
        f=TopoDS.Face_s(m.FindFromIndex(m.FindIndex(TopoDS.Edge_s(ex2.Current()))).First()); srf=BRep_Tool.Surface_s(f)
        if id(srf) not in seen: seen.add(id(srf)); cands.append(srf)
        ex2.Next()
    pf0=BRepBuilderAPI_MakeFace(w,True)
    if pf0.IsDone(): cands=[None]+cands
    best=None; why=[]
    for srf in cands:
        try:
            pf=pf0.Face() if srf is None else BRepBuilderAPI_MakeFace(srf,w,True).Face()
            sf=ShapeFix_Face(pf); sf.Perform(); pf=sf.Face(); a=area(pf)
            if a<=1e-3: why.append("tiny"); continue
            sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s); sw.Add(pf); sw.Perform(); sh=sw.SewedShape()
            if count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE)>=n0: why.append("nosew"); continue
            if not local_ok(pf): why.append("selfint"); continue
            best=(pf,"plane" if srf is None else "neighbour",a); break
        except Exception as e: why.append("err")
    if best: ok.append(best[0]); print("OK  ",tag,best[1],round(best[2],2),flush=True)
    else: print("OPEN",tag,why,flush=True)
    ex.Next()
sw=BRepBuilderAPI_Sewing(1e-4); sw.Add(s)
for f in ok: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,sys.argv[2])
print("patched",len(ok),"| loops left",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),flush=True)
