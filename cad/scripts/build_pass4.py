"""Pass 4 of the Gun structure cleanup: close every remaining open part.

usage: python build_pass4.py <pass3.step> <pass4.step>

* base (yaw housing)      rebuilt from clean sections + mirrored tray walls (geobase.py)
* 083 arm + 080/081/066   arm closed with exact flat faces; blocks rebuilt (geoarm.py)
* 097 slider              closed with exact flat faces
* 065                     closed with exact flat faces
* screws, pins, clip      plain solids instead of loose thread / head surfaces
* stray caps and faces that duplicate rebuilt parts are removed
"""
import sys
from asm_edit import Asm, compound
from geobase import build_base
import geoarm, heal
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_SOLID
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB

SRC, OUT = sys.argv[1], sys.argv[2]


def check(tag, s):
    n = 0; e = TopExp_Explorer(s, TopAbs_SOLID)
    while e.More(): n += 1; e.Next()
    ok = BRepCheck_Analyzer(s).IsValid()
    print(tag, 'valid', ok, 'solids', n)
    assert ok and n >= 1, tag


a = Asm(SRC)
parts = {k: a.shape(k) for k in a.keys()}

s = build_base(parts['base']); check('base', s); a.replace('base', s)
s = geoarm.build_arm(parts); check('083 arm', s); a.replace('083', s)
s = geoarm.build_slider(parts); check('097 slider', s); a.replace('097', s)
s, rep = heal.close(parts['065'], tol=0.02); check('065', s); a.replace('065', s)

brass = Quantity_Color(0.75, 0.62, 0.3, Quantity_TOC_RGB)
for k, shp in geoarm.build_fasteners().items():
    check('fastener ' + k, shp)
    if k in a.comp: a.replace(k, shp)
    else: a.add(k, shp, a.colour('001') or brass)

a.remove([k for k in geoarm.DROP if k in a.comp])
a.write(OUT, 'Scope/gimbal structure - cleanup pass 4: every part closed (base, arm, slider rebuilt; fasteners simplified; stray caps removed)')
print('written', OUT)
