exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.gp import gp_Pln, gp_Pnt, gp_Dir, gp_Ax2
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.BRep import BRep_Tool
from OCP.TopLoc import TopLoc_Location
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.GCPnts import GCPnts_QuasiUniformDeflection
cur=rd("work/p244_d8.brep"); pre=rd("work/p244_pre223.brep"); P=rd("work/cur_P223.brep")
bore=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-267.9,245),gp_Dir(0,0,1)),12.7,296.63-245).Shape()
def sec(solid,pl,rng):
    f=BRepBuilderAPI_MakeFace(pl,*rng).Face(); return BRepAlgoAPI_Common(solid,f).Shape()
def tris(sh,ij):
    BRepMesh_IncrementalMesh(sh,0.05,False,0.2,True); out=[]; ex=TopExp_Explorer(sh,TopAbs_FACE)
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is not None:
            tr=loc.Transformation(); N=[t.Node(i).Transformed(tr) for i in range(1,t.NbNodes()+1)]
            for k in range(1,t.NbTriangles()+1):
                a,b,c=t.Triangle(k).Get(); out.append([[getattr(N[q-1],ij[0])(),getattr(N[q-1],ij[1])()] for q in (a,b,c)])
        ex.Next()
    return out
def edges(sh,ij):
    L=[]; ex=TopExp_Explorer(sh,TopAbs_EDGE)
    while ex.More():
        c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.02)
        L.append(np.array([[getattr(d.Value(k),ij[0])(),getattr(d.Value(k),ij[1])()] for k in range(1,d.NbPoints()+1)])); ex.Next()
    return L
views=[("x = 0 (centre)",gp_Pln(gp_Pnt(0,0,0),gp_Dir(1,0,0)),(-1000,1000,-1000,1000),("Z","Y"),(245,305,-290,-245)),
       ("x = 8",gp_Pln(gp_Pnt(8,0,0),gp_Dir(1,0,0)),(-1000,1000,-1000,1000),("Z","Y"),(245,305,-290,-245)),
       ("x = 14.5 (side)",gp_Pln(gp_Pnt(14.5,0,0),gp_Dir(1,0,0)),(-1000,1000,-1000,1000),("Z","Y"),(245,305,-290,-245)),
       ("z = 275 (cross-section)",gp_Pln(gp_Pnt(0,0,275),gp_Dir(0,0,1)),(-1000,1000,-1000,1000),("X","Y"),(-24,24,-290,-245))]
fig,axs=plt.subplots(2,4,figsize=(30,15))
for col,(title,pl,rng,ij,lim) in enumerate(views):
    sP=sec(P,pl,rng); sC=sec(cur,pl,rng); sPre=sec(pre,pl,rng)
    prop=BRepAlgoAPI_Cut(BRepAlgoAPI_Cut(sPre,BRepAlgoAPI_Common(sP,sPre).Shape() if False else sP).Shape(),sec(bore,pl,rng)).Shape()
    for row,(sh,lab,colr) in enumerate([(sC,"FIXED P244",(.55,.55,.6)),(prop,"PLAN (target)",(.35,.55,.9))]):
        ax=axs[row,col]
        ax.add_collection(PolyCollection(tris(sh,ij),facecolors=colr,edgecolors='none'))
        ax.add_collection(PolyCollection(tris(sP,ij),facecolors=(1,.3,.3,.18),edgecolors='none'))
        for e in edges(sP,ij): ax.plot(e[:,0],e[:,1],'r-',lw=1.2)
        if row==1:
            # what changes vs now: added back (green outline)
            add=BRepAlgoAPI_Cut(prop,sC).Shape(); rem=BRepAlgoAPI_Cut(sC,prop).Shape()
            from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
            ex_=TopExp_Explorer(add,TopAbs_FACE)
            while ex_.More():
                g=GProp_GProps(); BRepGProp.SurfaceProperties_s(ex_.Current(),g)
                if abs(g.Mass())<300: ax.add_collection(PolyCollection(tris(ex_.Current(),ij),facecolors=(.2,.8,.3,.9),edgecolors='none'))
                ex_.Next()
            from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
            ex_=TopExp_Explorer(rem,TopAbs_FACE)
            while ex_.More():
                g=GProp_GProps(); BRepGProp.SurfaceProperties_s(ex_.Current(),g)
                if abs(g.Mass())<200: ax.add_collection(PolyCollection(tris(ex_.Current(),ij),facecolors=(1,.6,0,.9),edgecolors='none'))
                ex_.Next()
        ax.set_xlim(lim[0],lim[1]); ax.set_ylim(lim[2],lim[3]); ax.set_aspect('equal'); ax.grid(alpha=.25)
        ax.set_title(f"{lab} — {title}",fontsize=13); ax.set_xlabel(ij[0].lower()+" (mm)"); ax.set_ylabel(ij[1].lower()+" (mm)")
fig.suptitle("P244 rear tower — grey/blue = P244, red = P223 (upper receiver), green = material added back, orange = material removed",fontsize=16)
plt.tight_layout(rect=(0,0,1,0.96)); plt.savefig("work/check_sections.png",dpi=55); print("ok")
