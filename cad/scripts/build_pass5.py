"""Pass 5: attach the camera box to the slider 097.

The rectangular cable slot in the box's -Y wall (X -5.36..6.54, Z -39.02..30.98)
faces the slider 097 across a 3 mm gap (box wall Y -188.85, slider face
Y -191.85).  A 2 mm rectangular collar around the slot bridges that gap.

usage: python build_pass5.py <pass4.step> <pass5.step>
"""
import sys
from asm_edit import Asm
from geo270 import box, cut
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB

SRC, OUT = sys.argv[1], sys.argv[2]
Y_SLIDER, Y_BOX, T = -191.85, -188.85, 2.0
SX0, SX1, SZ0, SZ1 = -5.36, 6.54, -39.02, 30.98          # slot in the box wall
collar = cut(box(SX0 - T, Y_SLIDER, SZ0 - T, SX1 + T, Y_BOX, SZ1 + T),
             box(SX0, Y_SLIDER - 1, SZ0, SX1, Y_BOX + 1, SZ1))
assert BRepCheck_Analyzer(collar).IsValid()

a = Asm(SRC)
a.add('CAMERA_MOUNT', collar, Quantity_Color(0.55, 0.57, 0.6, Quantity_TOC_RGB))
a.write(OUT, 'Scope/gimbal structure - cleanup pass 5: camera box attached to slider 097 with a collar around its slot')
print('written', OUT)
