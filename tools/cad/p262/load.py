import sys, collections
from OCP.STEPControl import STEPControl_Reader
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE, TopAbs_SOLID, TopAbs_SHELL
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopoDS import TopoDS
def load(p):
    r=STEPControl_Reader(); r.ReadFile(p); r.TransferRoots(); return r.OneShape()
def bb(s):
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); m=b.CornerMin();M=b.CornerMax(); return [round(v,2) for v in (m.X(),m.Y(),m.Z(),M.X(),M.Y(),M.Z())]
def vol(s):
    g=GProp_GProps(); BRepGProp.VolumeProperties_s(s,g); return g.Mass()
def area(s):
    g=GProp_GProps(); BRepGProp.SurfaceProperties_s(s,g); return g.Mass()
def faces(s):
    e=TopExp_Explorer(s,TopAbs_FACE); out=[]
    while e.More(): out.append(TopoDS.Face_s(e.Current())); e.Next()
    return out
