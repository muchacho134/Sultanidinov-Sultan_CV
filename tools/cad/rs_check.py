exec(open("hous_dev.py").read().split("S=rd(")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.STEPControl import STEPControl_Writer, STEPControl_Reader, STEPControl_AsIs
from OCP.TopoDS import TopoDS_Compound
from OCP.BRep import BRep_Builder
S=rd("work/rs_solid.brep")
print("check ok (no self-int):",BRepAlgoAPI_Check(S,True,True).IsValid())
w=STEPControl_Writer(); w.Transfer(S,STEPControl_AsIs); w.Write("work/rs_solid.step")
r=STEPControl_Reader(); r.ReadFile("work/rs_solid.step"); r.TransferRoots(); R=r.OneShape(); print("roundtrip",vol(S),vol(R),count(R,TopAbs_SOLID))
names="P144 P145 P147 P148 P149 P230 P232 P233 P234 P235 P236 P240 P241 P243 solid_146 solid_226 solid_231 solid_237 solid_238 solid_239 solid_242".split()
for nm in names:
    O=rd(f"work/g_{nm}.brep"); ex=TopExp_Explorer(O,TopAbs_FACE); res=[]
    while ex.More():
        f=TopoDS.Face_s(ex.Current()); g=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,g)
        u0,u1,v0,v1=BRepTools.UVBounds_s(f); cl=BRepTopAdaptor_FClass2d(f,1e-6); sf=BRep_Tool.Surface_s(f); dm=[]
        for a in np.linspace(0.1,0.9,4):
            for b in np.linspace(0.1,0.9,4):
                uv=gp_Pnt2d(u0+a*(u1-u0),v0+b*(v1-v0))
                if cl.Perform(uv)==TopAbs_IN and len(dm)<6:
                    d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(sf.Value(uv.X(),uv.Y())).Vertex(),S); d.Perform(); dm.append(d.Value())
        if dm: res.append((np.median(dm),abs(g.Mass())))
        ex.Next()
    R_=np.array(res); A_=R_[:,1].sum()
    print(f"{nm:10s} area {A_:7.1f}  on new surface(<0.02mm) {R_[R_[:,0]<0.02,1].sum()/A_*100:5.1f}%  within 0.3mm {R_[R_[:,0]<0.3,1].sum()/A_*100:5.1f}%  max {R_[:,0].max():.2f}")
