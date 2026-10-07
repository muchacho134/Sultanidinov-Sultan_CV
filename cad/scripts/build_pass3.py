"""Pass 3 of the Gun structure cleanup.

usage: python build_pass3.py <pass2.step> <pass3.step>

* part 012 (side plate): broken hole pattern rebuilt (see geo012.py)
* camera box 272 + 273 -> one hollow box with the original outer surface
* its contents 274-587 (round unit, camera board, lens, camera) -> simple solids
* 014: stray cap face that filled 012's 45-deg counterbore -> removed
"""
import sys
from asm_edit import Asm, compound
from geo012 import build_012
from geocam import build_box, build_contents
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID, TopAbs_SHELL
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB

SRC, OUT = sys.argv[1], sys.argv[2]


def check(tag, s, nsolids=1):
    n = 0; e = TopExp_Explorer(s, TopAbs_SOLID)
    while e.More(): n += 1; e.Next()
    ok = BRepCheck_Analyzer(s).IsValid()
    print(tag, 'valid', ok, 'solids', n)
    assert ok and n == nsolids, tag


a = Asm(SRC)

s012 = build_012(a.shape('012')); check('012', s012)
a.replace('012', s012)

box = build_box(); check('camera box', box)
col = a.colour('272')
inside = [k for k in a.keys() if k.isdigit() and 272 <= int(k) <= 587]
a.remove(inside)
a.add('272_CAMERA_BOX', box, col)
grey = Quantity_Color(0.25, 0.25, 0.27, Quantity_TOC_RGB)
cols = {'ROUND_UNIT': Quantity_Color(0.55, 0.55, 0.58, Quantity_TOC_RGB), 'LENS': grey,
        'CAMERA_BOARD': Quantity_Color(0.15, 0.4, 0.2, Quantity_TOC_RGB), 'CAMERA': grey}
for k, v in build_contents().items():
    shp = compound(v) if isinstance(v, list) else v
    check(k, shp, len(v) if isinstance(v, list) else 1)
    a.add(k, shp, cols[k])

a.remove(['014'])
a.write(OUT, 'Scope/gimbal structure - cleanup pass 3: part 012 hole pattern rebuilt; camera box 272+273 as hollow box, contents 274-587 simplified')
print('written', OUT)
