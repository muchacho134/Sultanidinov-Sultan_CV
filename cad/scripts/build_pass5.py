"""Pass 5: simple U-bracket (two side walls + bottom plate) joining the camera
box to the front bearing block of the rail.

usage: python build_pass5.py <pass4.step> <pass5.step>
"""
import sys
from asm_edit import Asm
from geo270 import box, fuse_many
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB

SRC, OUT = sys.argv[1], sys.argv[2]
Y0, Y1 = -220.4, -188.85          # rail block front face -> camera box back wall
X0, X1, T = -45.0, -23.0, 3.0      # rail block width, wall thickness
Z0, Z1 = -61.0, 38.0               # bottom of block 035 -> top of camera box

mount = fuse_many([box(X0, Y0, Z0, X0 + T, Y1, Z1),       # wall at X -45
                   box(X1 - T, Y0, Z0, X1, Y1, Z1),       # wall at X -23
                   box(X0, Y0, Z0, X1, Y1, Z0 + T)])      # bottom plate
a = Asm(SRC)
# wrap around the parts already in that gap instead of overlapping them
from geo270 import cut
for k in ('012', '016', '083'):
    m2 = cut(mount, a.shape(k))
    if BRepCheck_Analyzer(m2).IsValid(): mount = m2
assert BRepCheck_Analyzer(mount).IsValid()

a.add('CAMERA_MOUNT', mount, Quantity_Color(0.55, 0.57, 0.6, Quantity_TOC_RGB))
a.write(OUT, 'Scope/gimbal structure - cleanup pass 5: camera box attached to the rail with a simple U-bracket')
print('written', OUT)
