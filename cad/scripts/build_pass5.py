"""Pass 5: attach the camera box to the arm with two small walls.

The box's -Y wall (Y -188.85) sits 9.75 mm above a flat face of the arm 083
(Y -198.6).  Two plain walls bridge that gap, one on each side of the slider.

usage: python build_pass5.py <pass4.step> <pass5.step>
"""
import sys
from asm_edit import Asm, compound
from geo270 import box
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB

SRC, OUT = sys.argv[1], sys.argv[2]
Y_ARM, Y_BOX = -198.6, -188.85
Z0, Z1 = -40.0, 37.0
walls = [box(-10.8, Y_ARM, Z0, -9.0, Y_BOX, Z1),     # left of the slider
         box(10.0, Y_ARM, Z0, 12.5, Y_BOX, Z1)]      # right of the slider
mount = compound(walls)
assert BRepCheck_Analyzer(mount).IsValid()

a = Asm(SRC)
a.add('CAMERA_MOUNT', mount, Quantity_Color(0.55, 0.57, 0.6, Quantity_TOC_RGB))
a.write(OUT, 'Scope/gimbal structure - cleanup pass 5: camera box attached to the arm with two small walls')
print('written', OUT)
