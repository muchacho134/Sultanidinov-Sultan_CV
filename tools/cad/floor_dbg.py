import sys, json, os
exec(open("split_fill.py").read().split("new=[]")[0].replace("spec=json.loads(open(sys.argv[3]).read())","spec=[]"))
from OCP.gp import gp_Trsf, gp_Vec, gp_Pln, gp_Pnt, gp_Dir
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakePolygon
from OCP.BRepFill import BRepFill
near=json.loads(sys.argv[3]); idx=json.loads(sys.argv[4]); YH=float(sys.argv[5])
L=min(loops,key=lambda l:(l[0]-near[0])**2+(l[1]-near[1])**2+(l[2]-near[2])**2); E=L[3]
new=[]; floorw=BRepBuilderAPI_MakeWire(); prev=None
from OCP.GC import GC_MakeArcOfCircle
from OCP.BRepAdaptor import BRepAdaptor_Curve
def lift(e,dy):
    c=BRepAdaptor_Curve(e); u0,u1=c.FirstParameter(),c.LastParameter()
    if e.Orientation()==1: u0,u1=u1,u0   # TopAbs_REVERSED
    pa=c.Value(u0); pm=c.Value((u0+u1)/2); pb=c.Value(u1)
    L=lambda p:gp_Pnt(p.X(),p.Y()+dy,p.Z())
    straight=pa.Distance(pb)>0 and abs(pa.Distance(pm)+pm.Distance(pb)-pa.Distance(pb))<1e-4
    if straight: return BRepBuilderAPI_MakeEdge(L(pa),L(pb)).Edge()
    return BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(L(pa),L(pm),L(pb)).Value()).Edge()
def P(p): return gp_Pnt(p.X(),YH,p.Z())
fpts=[]
for i in idx:
    e=E[i]; a,b=ends(e)
    ya,yb=a.Y(),b.Y()
    if abs(ya-YH)<1e-3 and abs(yb-YH)<1e-3: fe=e                       # already on floor level
    elif abs(ya-yb)<1e-3:                                               # red edge: strip + lifted copy
        fe=lift(e,YH-ya); fa,fb=ends(fe)
        new.append(BRepFill.Face_s(e,fe) if a.Distance(fa)<b.Distance(fa) else BRepFill.Face_s(e,TopoDS.Edge_s(fe.Reversed())))
    else:                                                               # transition: triangle(s)
        pa,pb=P(a),P(b)
        if a.Distance(pa)>1e-4 and b.Distance(pb)>1e-4:
            new.append(BRepBuilderAPI_MakeFace(BRepBuilderAPI_MakePolygon(a,b,pb,pa,True).Wire(),True).Face())
        elif a.Distance(pa)>1e-4: new.append(BRepBuilderAPI_MakeFace(BRepBuilderAPI_MakePolygon(a,b,pa,True).Wire(),True).Face())
        elif b.Distance(pb)>1e-4: new.append(BRepBuilderAPI_MakeFace(BRepBuilderAPI_MakePolygon(a,b,pb,True).Wire(),True).Face())
        fe=BRepBuilderAPI_MakeEdge(pa,pb).Edge() if pa.Distance(pb)>1e-4 else None
    if fe is not None: fpts.append(fe)
for fe in fpts:
    a,b=ends(fe)
    if prev is not None and prev.Distance(a)>1e-4: floorw.Add(BRepBuilderAPI_MakeEdge(prev,a).Edge())
    floorw.Add(fe); prev=b
for k,fe in enumerate(fpts):
    a,b=ends(fe); print("   fe",k,"(%.2f,%.2f,%.2f)->(%.2f,%.2f,%.2f)"%(a.X(),a.Y(),a.Z(),b.X(),b.Y(),b.Z()))
a0,_=ends(fpts[0])
if prev.Distance(a0)>1e-4: floorw.Add(BRepBuilderAPI_MakeEdge(prev,a0).Edge())
ff=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,YH,0),gp_Dir(0,1,0)),floorw.Wire(),True).Face()
sf=ShapeFix_Face(ff); sf.Perform(); ff=sf.Face(); print("floor area %.2f, strips/triangles %d"%(abs(area(ff)),len(new)))
new.append(ff)
# notch wall (plane) from extra edge list
if len(sys.argv)>6:
    nidx=json.loads(sys.argv[6]); mw=BRepBuilderAPI_MakeWire(); last=None; first=None
    for i in nidx:
        e=E[i]; a,b=ends(e)
        if last is not None and last.Distance(a)>1e-4: mw.Add(BRepBuilderAPI_MakeEdge(last,a).Edge())
        mw.Add(e); last=b; first=first or a
    if last.Distance(first)>1e-4: mw.Add(BRepBuilderAPI_MakeEdge(last,first).Edge())
    nf=BRepBuilderAPI_MakeFace(mw.Wire(),True).Face(); new.append(nf); print("notch area %.2f"%abs(area(nf)))
for k,f in enumerate(new): 
    if maxtol(f)>0.01: print("  face",k,"tol %.3f area %.3f"%(maxtol(f),area(f)))
sw=BRepBuilderAPI_Sewing(1e-3); sw.Add(s)
for f in new: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,sys.argv[2])
print("loops left",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),"maxtol %.4f"%maxtol(sh))
