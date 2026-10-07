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
cuts.append(halfspace((0.006,-243.9,-243.5),(0,0,1)))            # front face
cuts.append(halfspace((0.006,-243.9,-235.0),(0,0,1)))            # back face
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
for c in cuts:
    op=BRepAlgoAPI_Common(s,c); op.Build(); s=op.Shape()
u=ShapeUpgrade_UnifySameDomain(s,True,True,True); u.Build(); s=u.Shape()
so=TopExp_Explorer(s,TopAbs_SOLID).Current()
p=GProp_GProps(); BRepGProp.VolumeProperties_s(so,p); nf=0; ex=TopExp_Explorer(so,TopAbs_FACE)
while ex.More(): nf+=1; ex.Next()
print("collar: valid",BRepCheck_Analyzer(so).IsValid(),"| faces",nf,"| volume %.1f"%p.Mass())
BRepTools.Write_s(so,"work/collar.brep")
# compare with the original outer faces (the big analytic faces, excluding letters/marks)
orig=TopoDS_Shape(); BRepTools.Read_s(orig,"work/x_P111.brep",BRep_Builder())
keep=[2,4,5,9,21,22,23,24,25,26,27,28,29,36,37,38,48]
def faces(sh):
    L=[]; ex=TopExp_Explorer(sh,TopAbs_FACE)
    while ex.More(): L.append(TopoDS.Face_s(ex.Current())); ex.Next()
    return L
OF=faces(orig); cmp=TopoDS_Compound(); bb=BRep_Builder(); bb.MakeCompound(cmp)
for i in keep: bb.Add(cmp,OF[i])
def pts(sh,step=25):
    BRepMesh_IncrementalMesh(sh,0.05,False,0.2); out=[]
    for f in faces(sh):
        loc=TopLoc_Location(); t=BRep_Tool.Triangulation_s(f,loc)
        if t is None: continue
        for i in range(1,t.NbNodes()+1,max(1,t.NbNodes()//step)): out.append(t.Node(i).Transformed(loc.Transformation()))
    return out
def maxdist(P,target):
    w=0; worst=None
    for q in P:
        d=BRepExtrema_DistShapeShape(BRepBuilderAPI_MakeVertex(q).Vertex(),target); d.Perform()
        if d.Value()>w: w=d.Value(); worst=(q.X(),q.Y(),q.Z())
    return w,worst
oc=TopoDS_Compound(); bb.MakeCompound(oc)
for i in keep: bb.Add(oc,OF[i])
w1,p1=maxdist(pts(oc),so); print("original outer faces -> new collar surface: max %.4f mm at %s"%(w1,np.round(p1,2) if p1 else None))
w2,p2=maxdist(pts(so),cmp); print("new collar surface -> original outer faces: max %.4f mm at %s"%(w2,np.round(p2,2) if p2 else None))
