import sys, json
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepOffsetAPI import BRepOffsetAPI_MakeFilling
from OCP.GeomAbs import GeomAbs_C0
from OCP.BRepBuilderAPI import BRepBuilderAPI_Copy, BRepBuilderAPI_MakeEdge, BRepBuilderAPI_MakeWire
from OCP.BRepTools import BRepTools_WireExplorer
from OCP.BRep import BRep_Tool
from OCP.TopExp import TopExp
s=rd(sys.argv[1]); spec=json.loads(open(sys.argv[3]).read())
def maxtol(sh):
    mt=0; e=TopExp_Explorer(sh,TopAbs_EDGE)
    while e.More(): mt=max(mt,BRep_Tool.Tolerance_s(TopoDS.Edge_s(e.Current()))); e.Next()
    return mt
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
fb=ShapeAnalysis_FreeBounds(s,1e-4); loops=[]; ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_WIRE)
while ex.More():
    w=TopoDS.Wire_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(w,b,False,False); x=b.Get()
    E=[]; we=BRepTools_WireExplorer(w)
    while we.More(): E.append(TopoDS.Edge_s(BRepBuilderAPI_Copy(we.Current()).Shape())); we.Next()
    loops.append(((x[0]+x[3])/2,(x[1]+x[4])/2,(x[2]+x[5])/2,E)); ex.Next()
def pt(v): p=BRep_Tool.Pnt_s(v); return p
def ends(e):
    a=TopExp.FirstVertex_s(e,True); b=TopExp.LastVertex_s(e,True); return pt(a),pt(b)
new=[]
for job in spec:
    c=job["near"]; L=min(loops,key=lambda l:(l[0]-c[0])**2+(l[1]-c[1])**2+(l[2]-c[2])**2); E=L[3]
    if job.get("show"):
        for i,e in enumerate(E):
            a,b=ends(e); print(f"  {i:2d} ({a.X():7.2f},{a.Y():8.2f},{a.Z():7.2f}) -> ({b.X():7.2f},{b.Y():8.2f},{b.Z():7.2f})")
        continue
    for gi,g in enumerate(job["groups"]):
        if isinstance(g,dict) and "loft" in g:
            from OCP.BRepOffsetAPI import BRepOffsetAPI_ThruSections
            ws=[]
            for k,ch in enumerate(g["loft"]):
                mw=BRepBuilderAPI_MakeWire()
                seq=[E[i] for i in ch]
                if k==1: seq=[TopoDS.Edge_s(e_.Reversed()) for e_ in reversed(seq)]
                for e_ in seq: mw.Add(e_)
                ws.append(mw.Wire())
            ts=BRepOffsetAPI_ThruSections(False,True,1e-6); ts.AddWire(ws[0]); ts.AddWire(ws[1]); ts.CheckCompatibility(g.get("compat",True)); ts.Build()
            fx=TopExp_Explorer(ts.Shape(),TopAbs_FACE); tot=0
            while fx.More(): f=TopoDS.Face_s(fx.Current()); tot+=area(f); new.append(f); fx.Next()
            print(job.get("name",""),g,"loft area %.2f tol %.4f"%(tot,maxtol(ts.Shape()))); continue
        if isinstance(g,dict) and "rule_chord" in g:
            from OCP.BRepFill import BRepFill
            e1=E[g["rule_chord"]]; a1,b1=ends(e1); ch=BRepBuilderAPI_MakeEdge(a1,b1).Edge()
            f=BRepFill.Face_s(e1,ch); print(job.get("name",""),g,"ruled-chord area %.2f tol %.4f"%(area(f),maxtol(f))); new.append(f); continue
        if isinstance(g,dict) and "ruled" in g:
            from OCP.BRepFill import BRepFill
            e1=E[g["ruled"][0]]; e2=E[g["ruled"][1]]; a1,b1=ends(e1); a2,b2=ends(e2)
            if a1.Distance(a2)+b1.Distance(b2) > a1.Distance(b2)+b1.Distance(a2): e2=TopoDS.Edge_s(e2.Reversed())
            f=BRepFill.Face_s(e1,e2); print(job.get("name",""),g,"ruled area %.2f tol %.4f"%(area(f),maxtol(f))); new.append(f); continue
        pln=None; force_fill=False
        if isinstance(g,dict): surf=g.get("cyl"); pln=g.get("plane"); force_fill=g.get("fill",False); g=g["e"]
        else: surf=None
        idx=(list(range(g[0],g[1]+1)) if g[0]<=g[1] else list(range(g[0],len(E)))+list(range(0,g[1]+1))) if len(g)==2 and not job.get("explicit") else g
        mw=BRepBuilderAPI_MakeWire(); last=None; first=None
        from OCP.gp import gp_Pnt
        for i in idx:
            if isinstance(i,list) and i[0]=="bs":
                from OCP.GeomAPI import GeomAPI_PointsToBSpline
                from OCP.TColgp import TColgp_Array1OfPnt
                pts=i[1]; cand=[q for e_ in E for q in ends(e_)]
                pe_=gp_Pnt(*pts[-1]); qb=min(cand,key=lambda q:q.Distance(pe_))
                if qb.Distance(pe_)<0.02: pe_=qb
                arr=TColgp_Array1OfPnt(1,len(pts)+1); arr.SetValue(1,last)
                for k_,q_ in enumerate(pts[:-1]): arr.SetValue(k_+2,gp_Pnt(*q_))
                arr.SetValue(len(pts)+1,pe_)
                cv=GeomAPI_PointsToBSpline(arr,3,8,GeomAbs_C2 if False else __import__('OCP.GeomAbs',fromlist=['x']).GeomAbs_C2,1e-5).Curve()
                mw.Add(BRepBuilderAPI_MakeEdge(cv).Edge()); last=pe_; continue
            if isinstance(i,list) and i[0]=="arc":
                from OCP.GC import GC_MakeArcOfCircle
                pm_=gp_Pnt(*i[1:4]); pe_=gp_Pnt(*i[4:7])
                cand=[q for e_ in E for q in ends(e_)]; qb=min(cand,key=lambda q:q.Distance(pe_))
                if qb.Distance(pe_)<0.02: pe_=qb
                mw.Add(BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(last,pm_,pe_).Value()).Edge()); last=pe_; continue
            if isinstance(i,list):
                p=gp_Pnt(*i[1:])
                cand=[q for e_ in E for q in ends(e_)]
                qb=min(cand,key=lambda q:q.Distance(p))
                if qb.Distance(p)<0.02: p=qb
                if last is not None: mw.Add(BRepBuilderAPI_MakeEdge(last,p).Edge())
                last=p; first=first or p; continue
            e=E[i]; a,b=ends(e)
            if last is not None and last.Distance(a)>1e-3: mw.Add(BRepBuilderAPI_MakeEdge(last,a).Edge())
            mw.Add(e); last=b; first=first or a
        if last.Distance(first)>1e-3: mw.Add(BRepBuilderAPI_MakeEdge(last,first).Edge())
        w=mw.Wire(); mf=BRepBuilderAPI_MakeFace(w,True); how="plane"
        if pln=="auto":
            from OCP.gp import gp_Pln, gp_Pnt, gp_Dir, gp_Vec
            vs=[]; ev=TopExp_Explorer(w,TopAbs_VERTEX)
            while ev.More(): vs.append(BRep_Tool.Pnt_s(TopoDS.Vertex_s(ev.Current()))); ev.Next()
            best=None
            for a_ in range(len(vs)):
                for b_ in range(a_+1,len(vs)):
                    for c_ in range(b_+1,len(vs)):
                        n_=gp_Vec(vs[a_],vs[b_]).Crossed(gp_Vec(vs[a_],vs[c_]))
                        if best is None or n_.Magnitude()>best[0]: best=(n_.Magnitude(),vs[a_],n_)
            pln=[[best[1].X(),best[1].Y(),best[1].Z()],[best[2].X(),best[2].Y(),best[2].Z()]]
        if pln:
            from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
            f=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(*pln[0]),gp_Dir(*pln[1])),w,True).Face(); how="plane*"
        elif surf:
            from OCP.Geom import Geom_CylindricalSurface
            from OCP.gp import gp_Ax3, gp_Pnt, gp_Dir
            cs=Geom_CylindricalSurface((gp_Ax3(gp_Pnt(*surf[0]),gp_Dir(*surf[1]),gp_Dir(*surf[3])) if len(surf)>3 else gp_Ax3(gp_Pnt(*surf[0]),gp_Dir(*surf[1]))),surf[2]); f=BRepBuilderAPI_MakeFace(cs,w,True).Face(); how="cyl"
            _sf=ShapeFix_Face(f); _sf.Perform()
            if area(_sf.Face())<0: f=BRepBuilderAPI_MakeFace(cs,TopoDS.Wire_s(w.Reversed()),True).Face(); how="cyl-r"
        elif mf.IsDone() and not force_fill: f=mf.Face()
        else:
            how="fill"; fl=(BRepOffsetAPI_MakeFilling(3,15,2,False,1e-5,1e-4,0.01,0.1,8,9) if len(idx)>12 else BRepOffsetAPI_MakeFilling(3,40,4,False,1e-6,1e-5,0.01,0.1,10,30)); e2=TopExp_Explorer(w,TopAbs_EDGE)
            while e2.More(): fl.Add(TopoDS.Edge_s(e2.Current()),GeomAbs_C0); e2.Next()
            fl.Build(); f=TopoDS.Face_s(fl.Shape())
        sf=ShapeFix_Face(f); sf.Perform(); f=sf.Face()
        if area(f)<0: f=TopoDS.Face_s(f.Reversed())
        from OCP.BRepCheck import BRepCheck_Analyzer as _BA; print(job.get("name",""),g,how,"area %.2f tol %.4f"%(area(f),maxtol(f)),"valid",_BA(f).IsValid()); new.append(f)
if new:
    import os; sw=BRepBuilderAPI_Sewing(float(os.environ.get("SEWTOL","1e-3"))); sw.Add(s)
    for f in new: sw.Add(f)
    sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,sys.argv[2])
    print("loops left",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),"maxtol %.4f"%maxtol(sh))
