"""Pass 2 of the Gun structure cleanup.

usage: python build.py <pass1.step> <pass2.step>

* merges the linear-rail assembly (blocks 043/052/025/035, both rods, tube 020,
  bushings 023/024, bearing fragments 027-063, end supports 017/018) into one solid
* rebuilds part 270 as a closed solid following its 8-fold pattern
"""
import sys
from step_io import load
from geo270 import build_270, fuse_many, unify
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_SHELL, TopAbs_FACE
from OCP.TopoDS import TopoDS
from OCP.TDF import TDF_LabelSequence, TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TCollection import TCollection_ExtendedString, TCollection_HAsciiString
from OCP.TopLoc import TopLoc_Location
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorSurf, XCAFDoc_ColorGen
from OCP.Quantity import Quantity_Color
from OCP.STEPCAFControl import STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.Interface import Interface_Static
from OCP.ShapeFix import ShapeFix_Shape
from OCP.GProp import GProp_GProps
from OCP.BRepGProp import BRepGProp

SRC_IN, OUT = sys.argv[1], sys.argv[2]
PREFIX = '\\X2\\c870c900acbd\\X0\\ + \\X2\\c9d0bc8c\\X0\\ + \\X2\\c18ccd1d\\X0\\'

def cnt(s, t):
    e = TopExp_Explorer(s, t); n = 0
    while e.More(): n += 1; e.Next()
    return n
def report(tag, s):
    p = GProp_GProps(); BRepGProp.VolumeProperties_s(s, p)
    print(tag, 'valid', BRepCheck_Analyzer(s).IsValid(), 'solids', cnt(s, TopAbs_SOLID),
          'shells', cnt(s, TopAbs_SHELL), 'faces', cnt(s, TopAbs_FACE), 'vol %.1f' % p.Mass())
def cyl(x, y, z0, z1, r):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x, y, z0), gp_Dir(0, 0, 1)), r, z1 - z0).Shape()

parts, doc, st, root = load(SRC_IN)
ids = lambda a, b: ['%03d' % i for i in range(a, b + 1)]

# ---------- linear-rail frame: 2 rods + 4 bearing blocks + tube + end bushings + end supports ----------
COL1 = ['043', '052', '020', '022', '024'] + [i for i in ids(44, 63) if i != '052']
COL2 = ['025', '035', '021', '023'] + [i for i in ids(27, 42) if i != '035']
ENDS = ['017', '018']
REMOVE = COL1 + COL2 + ENDS
# solid bodies kept as-is (all valid closed solids)
keep = ['043', '052', '025', '035', '020', '024', '017', '018']
for k in keep:
    assert BRepCheck_Analyzer(parts[k]).IsValid() and cnt(parts[k], TopAbs_SOLID) == 1, k
X0 = -34.0
fills = []
for Y in (-293.4, -237.4):
    fills.append(cyl(X0, Y, -162, 38, 4.0))                    # rod (replaces surface-only rod / bearing fragments)
    fills.append(cyl(X0, Y, -61, -31, 7.9))                    # filled bearing bore, upper block
    fills.append(cyl(X0, Y, -136, -106, 7.9))                  # filled bearing bore, lower block
    fills.append(cyl(X0, Y, 29.9, 38.0, 4.1))                  # close rod clearance in top support
    fills.append(cyl(X0, Y, -162.0, -153.9, 4.1))              # close rod clearance in bottom support
fills.append(cyl(X0, -293.4, -50, 30, 5.1))                    # fill tube bore
fills.append(cyl(X0, -237.4, -154, -134, 7.5))                 # end bushing 023 (was an open surface)
frame = fuse_many([parts[k] for k in keep] + fills)
frame = unify(frame)
report('frame', frame)
assert cnt(frame, TopAbs_SOLID) == 1 and BRepCheck_Analyzer(frame).IsValid()

p270 = build_270()
report('270', p270)
assert cnt(p270, TopAbs_SOLID) == 1 and BRepCheck_Analyzer(p270).IsValid()

# ---------- edit the assembly document ----------
ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
comps = TDF_LabelSequence(); st.GetComponents_s(root, comps)
def nm(l):
    n = TDataStd_Name()
    return n.Get().ToExtString() if l.FindAttribute(TDataStd_Name.GetID_s(), n) else ''
by = {}
for i in range(1, comps.Length() + 1):
    c = comps.Value(i); k = nm(c)[-3:]
    if k.isdigit(): by[k] = c
# colour of the original block, reused for the merged frame
col = Quantity_Color()
ref043 = TDF_Label(); st.GetReferredShape_s(by['043'], ref043)
from OCP.XCAFDoc import XCAFDoc_ColorTool
has_col = XCAFDoc_ColorTool.GetColor_s(ref043, XCAFDoc_ColorSurf, col) or XCAFDoc_ColorTool.GetColor_s(ref043, XCAFDoc_ColorGen, col)
print('colour', has_col, col.Red(), col.Green(), col.Blue())

for k in REMOVE:
    ref = TDF_Label(); st.GetReferredShape_s(by[k], ref)
    st.RemoveComponent(by[k])
    assert st.RemoveShape(ref, True), ('could not remove definition of', k)

# part 270: replace by the rebuilt solid (same name, colour and placement)
c270 = by['270']; r270 = TDF_Label(); st.GetReferredShape_s(c270, r270)
loc = st.GetLocation_s(c270)
name270 = nm(r270); cname270 = nm(c270); root_name = nm(root)
col270 = Quantity_Color()
has270 = XCAFDoc_ColorTool.GetColor_s(r270, XCAFDoc_ColorSurf, col270) or XCAFDoc_ColorTool.GetColor_s(r270, XCAFDoc_ColorGen, col270)
st.RemoveComponent(c270); assert st.RemoveShape(r270, True)
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
local270 = BRepBuilderAPI_Transform(p270, loc.Inverted().Transformation(), True).Shape()
assert BRepCheck_Analyzer(local270).IsValid()
l270 = st.AddShape(local270, False)
TDataStd_Name.Set_s(l270, TCollection_ExtendedString(name270))
if has270: ct.SetColor(l270, col270, XCAFDoc_ColorSurf)
cc = st.AddComponent(root, l270, loc)
TDataStd_Name.Set_s(cc, TCollection_ExtendedString(cname270))

# merged frame as a new part
lab = st.AddShape(frame, False)
TDataStd_Name.Set_s(lab, TCollection_ExtendedString(PREFIX + '043_052_RAIL_MERGED'))
if has_col: ct.SetColor(lab, col, XCAFDoc_ColorSurf)
cl = st.AddComponent(root, lab, TopLoc_Location())
TDataStd_Name.Set_s(cl, TCollection_ExtendedString(PREFIX + '043_052_RAIL_MERGED'))
st.UpdateAssemblies()
TDataStd_Name.Set_s(root, TCollection_ExtendedString(root_name))
print('names', name270[-3:], root_name[-3:])

Interface_Static.SetCVal_s('write.step.schema', 'AP214IS')
Interface_Static.SetCVal_s('write.step.unit', 'MM')
Interface_Static.SetIVal_s('write.surfacecurve.mode', 0)
w = STEPCAFControl_Writer(); w.SetNameMode(True); w.SetColorMode(True)
w.Transfer(doc, STEPControl_AsIs)
assert w.Write(OUT) == 1
# header: say what this pass did
import re
txt = open(OUT, encoding='latin-1').read()
txt = re.sub(r"FILE_DESCRIPTION\(\(.*?\),'2;1'\);",
             "FILE_DESCRIPTION(('Scope/gimbal structure - cleanup pass 2: linear rail (043/052 + rods, bearings, end supports) merged into one solid; part 270 rebuilt as closed solid'),'2;1');",
             txt, count=1, flags=re.S)
open(OUT, 'w', encoding='latin-1').write(txt)
print('written', OUT)
