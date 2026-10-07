import numpy as np
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2, gp_Pln, gp_Vec
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox, BRepPrimAPI_MakeHalfSpace, BRepPrimAPI_MakeCylinder, BRepPrimAPI_MakeCone
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeVertex
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Check
from OCP.ShapeUpgrade import ShapeUpgrade_UnifySameDomain
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import *
from OCP.TopoDS import TopoDS, TopoDS_Shape, TopoDS_Compound
from OCP.BRepTools import BRepTools
from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepMesh import BRepMesh_IncrementalMesh
from OCP.TopLoc import TopLoc_Location
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
C=np.array([0.006,-243.9,-239.25])                      # point inside the collar
AX=np.array([0.006,-243.9])
def halfspace(pt,n):
    pln=gp_Pln(gp_Pnt(*pt),gp_Dir(*n)); f=BRepBuilderAPI_MakeFace(pln,-200,200,-200,200).Face()
    return BRepPrimAPI_MakeHalfSpace(f,gp_Pnt(*C)).Solid()
s=BRepPrimAPI_MakeBox(gp_Pnt(-30,-270,-260),gp_Pnt(30,-220,-220)).Shape()
cuts=[]
cuts.append(halfspace((0,0,-243.5),(0,0,1)))            # front face
cuts.append(halfspace((0,0,-235.0),(0,0,1)))            # back face
cuts.append(halfspace((-1.486,-255.313,-240),(0.866,0.5001,0)))   # left flat
cuts.append(halfspace((10.418,-247.932,-240),(0.866,0.5001,0)))   # right flat
cuts.append(halfspace((10.418,-247.932,-243.0),(0.6123,0.3536,-0.7071)))   # right flat, front chamfer
cuts.append(halfspace((-5.622,-247.151,-243.5),(0.6123,0.3536,0.7071)))    # left flat, front chamfer
cuts.append(halfspace((-1.486,-255.313,-235.5),(-0.6123,-0.3536,0.7071)))  # left flat, back chamfer
# right flat, back chamfer (missing in file) = point-mirror of the left one through the collar axis plane-symmetry:
# take a point on the right flat at z=-235.5 and normal mirrored in x/y
rp=np.array([10.418,-247.932,-235.5]); cuts.append(halfspace(rp,(0.6123,0.3536,0.7071)))
cuts.append(BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(AX[0],AX[1],-260),gp_Dir(0,0,1)),9.4,40).Shape())
# chamfer cones: front (apex z=-251.9, opening +z), back (apex z=-226.1, opening -z)
cuts.append(BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(AX[0],AX[1],-251.9),gp_Dir(0,0,1)),0.0,30.0,30.0).Shape())
cuts.append(BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(AX[0],AX[1],-226.1),gp_Dir(0,0,-1)),0.0,30.0,30.0).Shape())
names=["front","back","left flat","right flat","R flat front chamf","L flat front chamf","L flat back chamf","R flat back chamf","cylinder","front cone","back cone"]
for nm,c in zip(names,cuts):
    op=BRepAlgoAPI_Common(s,c); op.Build(); s=op.Shape()
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); x=b.Get(); p=GProp_GProps(); BRepGProp.VolumeProperties_s(s,p)
    print("%-20s done=%s vol %.1f bbox x[%.2f,%.2f] y[%.2f,%.2f] z[%.2f,%.2f]"%(nm,op.IsDone(),p.Mass(),x[0],x[3],x[1],x[4],x[2],x[5]))
