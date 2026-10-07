import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.BRepFill import BRepFill_Filling
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.GeomAbs import GeomAbs_C0
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy
s=rd(sys.argv[1]); skip=set(int(a) for a in sys.argv[3].split(',')) if len(sys.argv)>3 else set()
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
def maxtol(sh):
    mt=0; e=TopExp_Explorer(sh,TopAbs_EDGE)
    while e.More(): mt=max(mt,BRep_Tool.Tolerance_s(TopoDS.Edge_s(e.Current()))); e.Next()
    return mt
fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE); ok=[]; k=-1
while ex.More():
    k+=1; w0=TopoDS.Wire_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(w0,b,False,False); x=b.Get(); ne=count(w0,TopAbs_EDGE)
    tag=f"#{k:2d} {ne:3d} edges x[{x[0]:.1f},{x[3]:.1f}] y[{x[1]:.1f},{x[4]:.1f}] z[{x[2]:.1f},{x[5]:.1f}]"
    res="FAIL"
    if k in skip: print(tag,"SKIP"); ex.Next(); continue
    try:
        wc=BRepBuilderAPI_Copy(w0).Shape(); mf=BRepOffsetAPI_MakeFilling(3,15,2,False,1e-5,1e-4,0.01,0.1,8,9)
        e=TopExp_Explorer(wc,TopAbs_EDGE)
        while e.More(): mf.Add(TopoDS.Edge_s(e.Current()),GeomAbs_C0); e.Next()
        mf.Build()
        if mf.IsDone():
            pf=TopoDS.Face_s(mf.Shape()); a=area(pf); pb=Bnd_Box(); BRepBndLib.AddOptimal_s(pf,pb,False,False); q=pb.Get()
            dev=max(abs(q[i]-x[i]) for i in range(6)); mt=maxtol(pf)
            res=f"area {a:.2f} tol {mt:.4f} bbdev {dev:.2f}"
            if mt<0.1 and dev<1.5 and a>1e-4: ok.append(pf); res="OK   "+res
    except Exception as ee: res="ERR "+str(ee)[:40]
    print(tag,res,flush=True); ex.Next()
sw=BRepBuilderAPI_Sewing(1e-3); sw.Add(s)
for f in ok: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,sys.argv[2])
print("filled",len(ok),"loops left",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),"maxtol",maxtol(sh),flush=True)
