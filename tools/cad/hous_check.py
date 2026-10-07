exec(open("barrel_fuse.py").read().split("pieces={}; caps=[]")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Check
from OCP.STEPControl import STEPControl_Writer, STEPControl_Reader, STEPControl_AsIs
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
import numpy as np
S=rd("work/hous_solid.brep")
c=BRepAlgoAPI_Check(S,True,True); print("selfint/check ok:",c.IsValid())
w=STEPControl_Writer(); w.Transfer(S,STEPControl_AsIs); w.Write("work/hous_solid.step")
r=STEPControl_Reader(); r.ReadFile("work/hous_solid.step"); r.TransferRoots(); R=r.OneShape()
print("roundtrip vol",vol(S),vol(R),"solids",count(R,TopAbs_SOLID))
# deviation: sample original outer faces vs new solid
O=rd("work/x_P596.brep"); from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeVertex
ex=TopExp_Explorer(O,TopAbs_FACE); ds=[]
while ex.More():
    f=TopoDS.Face_s(ex.Current()); g=GProp_GProps(); BRepGProp.SurfaceProperties_s(f,g); p=g.CentreOfMass()
    d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(p).Vertex(),S); d.Perform()
    from OCP.BRepClass3d import BRepClass3d_SolidClassifier
    ds.append((d.Value(),g.Mass())); ex.Next()
ds=np.array(ds); A=ds[:,1].sum()
for t in (0.01,0.1,0.5,1.6): print(f"area fraction of original faces within {t} mm of new surface: {ds[ds[:,0]<=t,1].sum()/A*100:.1f}%")
