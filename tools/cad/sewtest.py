import sys, pickle, numpy as np, collections
exec(open("puzzle.py").read().split("print(\"parts\",len(parts))")[0])
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
from OCP.ShapeFix import ShapeFix_Solid
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.TopTools import TopTools_IndexedMapOfShape
from OCP.BRepTools import BRepTools
res=pickle.load(open("work/freefree.pkl","rb")); W=res[0.5]
d=pickle.load(open("work/puzzle_pts.pkl","rb")); info=d['info']
def freelen(s):
    m=TopTools_IndexedDataMapOfShapeListOfShape(); TopExp.MapShapesAndAncestors_s(s,TopAbs_EDGE,TopAbs_FACE,m); L=0.0
    for i in range(1,m.Extent()+1):
        if m.FindFromIndex(i).Size()==1:
            try: L+=GCPnts_AbscissaPoint.Length_s(BRepAdaptor_Curve(TopoDS.Edge_s(m.FindKey(i))))
            except Exception: pass
    return L
# link rule
par={}
def f(x):
    par.setdefault(x,x)
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
for (a,b),L in W.items():
    if a>=b: continue
    L2=W.get((b,a),0); sh=max(L,L2)
    small=min(info[a]['freelen'],info[b]['freelen'])
    if sh>=1.0 and (sh>=10 or sh>=0.10*small): par[f(a)]=f(b)
comp=collections.defaultdict(list)
for k in info: comp[f(k)].append(k)
groups=sorted([sorted(v) for v in comp.values() if len(v)>1],key=len,reverse=True)
print("groups:",len(groups))
out=[]
for gi,G in enumerate(groups):
    before=sum(info[k]['freelen'] for k in G)
    best=None
    for tol in (0.05,0.2,0.5):
        sw=BRepBuilderAPI_Sewing(tol)
        for k in G: sw.Add(parts[k])
        sw.Perform(); r=sw.SewedShape()
        shells=[]; ex=TopExp_Explorer(r,TopAbs_SHELL)
        while ex.More(): shells.append(ex.Current()); ex.Next()
        after=sum(freelen(x) for x in shells)
        closed=sum(1 for x in shells if freelen(x)<1e-6)
        cand=(after,tol,len(shells),closed,r)
        if best is None or after<best[0]-1e-6: best=cand
    after,tol,nsh,closed,r=best
    out.append((gi,G,before,after,tol,nsh,closed))
    BRepTools.Write_s(r,f"work/group_{gi}.brep")
    print(f"G{gi}: {len(G)} parts | open boundary {before:.0f} -> {after:.0f} mm ({100*(1-after/max(before,1e-9)):.0f}% closed) at tol {tol} | shells {nsh}, fully closed {closed}")
    print("     ",", ".join(G))
pickle.dump(out,open("work/sewtest.pkl","wb"))
