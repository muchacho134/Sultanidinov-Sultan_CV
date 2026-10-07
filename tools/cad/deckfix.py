exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.gp import gp_Pnt
from OCP.GProp import GProp_GProps; from OCP.BRepGProp import BRepGProp
def area(f): p=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,p); return p.Mass()
s=rd("work/p244_s11.brep"); ex=TopExp_Explorer(s,TopAbs_FACE); keep=[]
box=BRepPrimAPI_MakeBox(gp_Pnt(-40,-290,0),gp_Pnt(40,-270,256.22)).Shape()
while ex.More():
    f=TopoDS.Face_s(ex.Current()); b=Bnd_Box(); BRepBndLib.AddOptimal_s(f,b,False,False); X=b.Get()
    deck=abs(X[1]+283.1)<0.02 and abs(X[4]+283.1)<0.02 and X[5]>256.5
    if deck and abs(area(f)-1.24)<0.05: print("drop dup"); ex.Next(); continue
    if deck and area(f)>100:
        from OCP.TopTools import TopTools_ListOfShape
        op=BRepAlgoAPI_Common(); A=TopTools_ListOfShape(); A.Append(f); T=TopTools_ListOfShape(); T.Append(box); op.SetArguments(A); op.SetTools(T); op.SetFuzzyValue(1e-4); op.Build(); c=op.Shape()
        if count(c,TopAbs_FACE)==0:
            from OCP.BRepAlgoAPI import BRepAlgoAPI_Splitter
            from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
            from OCP.gp import gp_Pln, gp_Dir
            pl=BRepBuilderAPI_MakeFace(gp_Pln(gp_Pnt(0,0,256.22),gp_Dir(0,0,1)),-50,50,-400,-200).Face()
            sp=BRepAlgoAPI_Splitter(); A=TopTools_ListOfShape(); A.Append(f); T=TopTools_ListOfShape(); T.Append(pl); sp.SetArguments(A); sp.SetTools(T); sp.Build()
            from OCP.TopoDS import TopoDS_Compound; from OCP.BRep import BRep_Builder as BB
            cc=TopoDS_Compound(); bb=BB(); bb.MakeCompound(cc); e3=TopExp_Explorer(sp.Shape(),TopAbs_FACE)
            while e3.More():
                g=e3.Current(); b3=Bnd_Box(); BRepBndLib.AddOptimal_s(g,b3,False,False)
                if b3.Get()[5]<256.25: bb.Add(cc,g)
                else: print("  drop piece %.2f"%area(TopoDS.Face_s(g)))
                e3.Next()
            c=cc
        e2=TopExp_Explorer(c,TopAbs_FACE); n=0
        while e2.More(): keep.append(e2.Current()); n+=1; print("trim %.2f -> %.2f"%(area(f),area(TopoDS.Face_s(e2.Current())))); e2.Next()
        ex.Next(); continue
    keep.append(f); ex.Next()
sw=BRepBuilderAPI_Sewing(0.003)
for f in keep: sw.Add(f)
sw.Perform(); sh=sw.SewedShape(); BRepTools.Write_s(sh,"work/p244_s12.brep")
