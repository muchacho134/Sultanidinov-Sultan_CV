exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepPrimAPI import BRepPrimAPI_MakePrism, BRepPrimAPI_MakeCylinder
from OCP.BRepAlgoAPI import BRepAlgoAPI_Cut, BRepAlgoAPI_Fuse
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.gp import gp_Vec, gp_Ax2, gp_Pnt, gp_Dir
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
g=rd("work/g_P244.brep"); so=rd("work/p244_solid2.brep")
ex=TopExp_Explorer(g,TopAbs_FACE); top=None
while ex.More():
    f=TopoDS.Face_s(ex.Current()); a=BRepAdaptor_Surface(f); b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); X=b.Get()
    if int(a.GetType())==0 and abs(X[1]+301.44)<0.05 and abs(X[4]+301.44)<0.05 and X[0]<-16: top=f; print("slot face x[%.2f,%.2f] z[%.2f,%.2f]"%(X[0],X[3],X[2],X[5]))
    ex.Next()
pr=BRepPrimAPI_MakePrism(top,gp_Vec(0,-6.6,0)).Shape()
cy=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(-16.75,-304.74,146.98),gp_Dir(1,0,0)),3.3,16.75-11.81).Shape()
tool=BRepAlgoAPI_Fuse(pr,cy).Shape()
print("tool vol %.1f"%vol(tool))
c=BRepAlgoAPI_Cut(so,tool); r=c.Shape()
print("cut valid",BRepCheck_Analyzer(r).IsValid(),"vol %.1f -> %.1f"%(vol(so),vol(r)),"solids",count(r,TopAbs_SOLID) if 'TopAbs_SOLID' in dir() else "")
BRepTools.Write_s(r,"work/p244_solid3.brep")
