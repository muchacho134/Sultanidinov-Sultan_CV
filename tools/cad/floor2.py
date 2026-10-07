import sys, json, math
exec(open("split_fill.py").read().split("new=[]")[0].replace("spec=json.loads(open(sys.argv[3]).read())","spec=[]"))
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir
from OCP.GC import GC_MakeArcOfCircle
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepFill import BRepFill
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
near=json.loads(sys.argv[3]); idx=json.loads(sys.argv[4]); YH=float(sys.argv[5]); YL=float(sys.argv[6]); OFF=float(sys.argv[7]); nidx=json.loads(sys.argv[8])
L=min(loops,key=lambda l:(l[0]-near[0])**2+(l[1]-near[1])**2+(l[2]-near[2])**2); E=L[3]
def samp(e):
    c=BRepAdaptor_Curve(e); u0,u1=c.FirstParameter(),c.LastParameter()
    if e.Orientation()==1: u0,u1=u1,u0
    return [c.Value(u0+(u1-u0)*t) for t in (0,0.25,0.5,0.75,1)]
items=[]
for i in idx:
    P=samp(E[i]); ys=[p.Y() for p in P]
    if max(abs(y-YH) for y in ys)<1e-3: kind="blue"
    elif max(abs(y-YL) for y in ys)<1e-3: kind="red"
    else: kind="trans"
    items.append([i,kind,P])
# orientation of loop in (x,z)
poly=[(p.X(),p.Z()) for it in items for p in it[2][:-1]]
A=sum(poly[k][0]*poly[(k+1)%len(poly)][1]-poly[(k+1)%len(poly)][0]*poly[k][1] for k in range(len(poly)))/2
sgn=1 if A>0 else -1      # CCW (A>0): interior on the left
def nrm(p,q):
    dx,dz=q.X()-p.X(),q.Z()-p.Z(); l=math.hypot(dx,dz); return (-dz/l*sgn,dx/l*sgn)
def offpts(P):
    out=[]
    for k,p in enumerate(P):
        a=P[max(k-1,0)]; b=P[min(k+1,len(P)-1)]; n=nrm(a,b); out.append(gp_Pnt(p.X()+OFF*n[0],YH,p.Z()+OFF*n[1]))
    return out
def straight(P): return abs(sum(P[k].Distance(P[k+1]) for k in range(len(P)-1))-P[0].Distance(P[-1]))<1e-5
chain=[]   # floor pieces: (kind, pa, pm, pb, src_edge or None)
for i,kind,P in items:
    if kind=="trans": continue
    if kind=="blue": chain.append(["edge",P[0],P[2],P[-1],E[i],None])
    else:
        if straight(P): Q=offpts(P); Q=[Q[0],Q[2],Q[-1]]
        else:
            c=BRepAdaptor_Curve(E[i])
            from OCP.GeomAbs import GeomAbs_Circle
            Q=offpts(P); Q=[Q[0],Q[2],Q[-1]]
            if c.GetType()==GeomAbs_Circle:
                ctr=c.Circle().Location(); r=c.Circle().Radius()
                mid=offpts(P)[2]; rn=math.hypot(mid.X()-ctr.X(),mid.Z()-ctr.Z())
                Q=[gp_Pnt(ctr.X()+(p.X()-ctr.X())*rn/r,YH,ctr.Z()+(p.Z()-ctr.Z())*rn/r) for p in (P[0],P[2],P[-1])]
        chain.append(["off",Q[0],Q[1],Q[2],E[i],straight(P)])
# miter consecutive straight offsets
def isect(p1,p2,p3,p4):
    x1,z1,x2,z2,x3,z3,x4,z4=p1.X(),p1.Z(),p2.X(),p2.Z(),p3.X(),p3.Z(),p4.X(),p4.Z()
    d=(x1-x2)*(z3-z4)-(z1-z2)*(x3-x4)
    if abs(d)<1e-12: return None
    t=((x1-x3)*(z3-z4)-(z1-z3)*(x3-x4))/d; return gp_Pnt(x1+t*(x2-x1),YH,z1+t*(z2-z1))
n=len(chain)
for k in range(n):
    c1=chain[k]; c2=chain[(k+1)%n]
    s1=c1[5] if c1[0]=="off" else abs(c1[1].Distance(c1[2])+c1[2].Distance(c1[3])-c1[1].Distance(c1[3]))<1e-6
    s2=c2[5] if c2[0]=="off" else abs(c2[1].Distance(c2[2])+c2[2].Distance(c2[3])-c2[1].Distance(c2[3]))<1e-6
    if c1[3].Distance(c2[1])>1e-4 and (c1[0]=="off" or c2[0]=="off") and s1 and s2 and c1[1].Distance(c1[3])>1e-4 and c2[1].Distance(c2[3])>1e-4:
        X=isect(c1[1],c1[3],c2[1],c2[3])
        if X and X.Distance(c1[3])<1.0 and X.Distance(c2[1])<1.0:
            if c1[0]=="off": c1[3]=X; c1[2]=gp_Pnt((c1[1].X()+X.X())/2,YH,(c1[1].Z()+X.Z())/2)
            if c2[0]=="off": c2[1]=X; c2[2]=gp_Pnt((X.X()+c2[3].X())/2,YH,(X.Z()+c2[3].Z())/2)
anchors=[]
for i in idx+nidx:
    a,b=ends(E[i])
    for p in (a,b):
        if abs(p.Y()-YH)<1e-3: anchors.append(p)
def snap(p):
    best=min(anchors,key=lambda q:q.Distance(p)) if anchors else None
    return gp_Pnt(best.X(),YH,best.Z()) if best is not None and best.Distance(p)<0.02 else p
for c in chain:
    c[1]=snap(c[1]); c[3]=snap(c[3])
for k in range(len(chain)):
    c1=chain[k]; c2=chain[(k+1)%len(chain)]; g=c1[3].Distance(c2[1])
    if 1e-4<g<0.1:
        if c1[0]=="off" and c1[5]: c1[3]=c2[1]; c1[2]=gp_Pnt((c1[1].X()+c1[3].X())/2,YH,(c1[1].Z()+c1[3].Z())/2)
        elif c2[0]=="off" and c2[5]: c2[1]=c1[3]; c2[2]=gp_Pnt((c2[1].X()+c2[3].X())/2,YH,(c2[1].Z()+c2[3].Z())/2)
for k,c in enumerate(chain):
    nx=chain[(k+1)%len(chain)][1]
    if c[3].Distance(nx)>1e-4: print('  gap after',k,c[0],'%.3f'%c[3].Distance(nx))
# build floor wire with shared vertices; gaps closed by lines
V=[]; mw=BRepBuilderAPI_MakeWire(); new=[]; offedges={}
pts=[]
for c in chain: pts.append(c[1])
def vert(p):
    for q,v in V:
        if q.Distance(p)<1e-4: return v
    from OCP.TopoDS import TopoDS_Vertex
    from OCP.BRep import BRep_Builder
    v=TopoDS_Vertex(); BRep_Builder().MakeVertex(v,p,2e-4); V.append((p,v)); return v
gaps=0
corner_faces=[]
for k,c in enumerate(chain):
    kind,pa,pm,pb,src,st=c
    va,vb=vert(pa),vert(pb)
    if kind=="edge" or st or pa.Distance(pb)<1e-4 or abs(pa.Distance(pm)+pm.Distance(pb)-pa.Distance(pb))<1e-6:
        e=BRepBuilderAPI_MakeEdge(va,vb).Edge() if pa.Distance(pb)>1e-4 else None
    else: e=BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(pa,pm,pb).Value(),va,vb).Edge()
    if kind=="edge" and src is not None:
        # use 3-point re-creation of the existing blue edge too (keeps shared vertices)
        if abs(pa.Distance(pm)+pm.Distance(pb)-pa.Distance(pb))>1e-6 and pa.Distance(pb)>1e-4: e=BRepBuilderAPI_MakeEdge(GC_MakeArcOfCircle(pa,pm,pb).Value(),va,vb).Edge()
    if e is not None: mw.Add(e)
    if kind=="off" and e is not None: offedges[k]=e
    nx=chain[(k+1)%n][1]
    if pb.Distance(nx)>1e-4:
        gaps+=1; mw.Add(BRepBuilderAPI_MakeEdge(vert(pb),vert(nx)).Edge())
        if pb.Distance(nx)<1.0:
            ra=ends(src)[1] if src is not None else None; nsrc=chain[(k+1)%n][4]; rb=ends(nsrc)[0] if nsrc is not None else None
            from OCP.BRepBuilderAPI import BRepBuilderAPI_MakePolygon
            P4=[pb,nx]
            if rb is not None and rb.Distance(nx)>1e-4: P4.append(rb)
            if ra is not None and ra.Distance(pb)>1e-4 and (rb is None or ra.Distance(rb)>1e-4): P4.append(ra)
            if len(P4)>=3:
                pg=BRepBuilderAPI_MakePolygon()
                for p in P4: pg.Add(p)
                pg.Close(); cf=BRepBuilderAPI_MakeFace(pg.Wire(),True)
                if cf.IsDone(): corner_faces.append(cf.Face())
print("loop orientation",sgn,"items",len(items),"floor pieces",len(chain),"gap lines",gaps, "wire ok",mw.IsDone())
ff=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,YH,0),gp_Dir(0,1,0)),mw.Wire(),True).Face(); print("floor area %.2f"%abs(area(ff))); new.append(ff)
new+=corner_faces; print('corner faces',len(corner_faces))
# chamfer strips
for k,e in offedges.items():
    src=chain[k][4]; a,b=ends(src); fa,fb=ends(e)
    f=BRepFill.Face_s(src,e) if a.Distance(fa)<a.Distance(fb) else BRepFill.Face_s(src,TopoDS.Edge_s(e.Reversed()))
    new.append(f)
# notch wall
mw2=BRepBuilderAPI_MakeWire(); last=None; first=None
for i in nidx:
    e=E[i]; a,b=ends(e)
    if last is not None and last.Distance(a)>1e-4: mw2.Add(BRepBuilderAPI_MakeEdge(last,a).Edge())
    mw2.Add(e); last=b; first=first or a
if last.Distance(first)>1e-4: mw2.Add(BRepBuilderAPI_MakeEdge(last,first).Edge())
new.append(BRepBuilderAPI_MakeFace(mw2.Wire(),True).Face())
bad=[k for k,f in enumerate(new) if maxtol(f)>0.01]; print("faces",len(new),"bad tol",bad)
sw=BRepBuilderAPI_Sewing(1e-3); sw.Add(s)
for f in new: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,sys.argv[2])
print("loops left",count(ShapeAnalysis_FreeBounds(sh,1e-4).GetClosedWires(),TopAbs_WIRE),"maxtol %.4f"%maxtol(sh))
