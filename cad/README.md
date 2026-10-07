# Gun structure STEP cleanup

| file | what changed |
|---|---|
| `Gun_structure_cleanup_pass1.step` | input |
| `Gun_structure_cleanup_pass2.step` | linear rail (043/052 + rods, bearings, end supports) merged into one solid; part 270 rebuilt as a closed solid |
| `Gun_structure_cleanup_pass3.step` | part 012 hole pattern rebuilt; camera box 272+273 as a hollow box; its contents simplified |
| `Gun_structure_cleanup_pass4.step` | every remaining part closed: `base` housing and 083 arm / 097 slider rebuilt, fasteners simplified, stray caps removed. All 34 parts are valid closed solids |
| `Gun_structure_cleanup_pass5.step` | camera box attached to the arm with two small walls (`CAMERA_MOUNT`) bridging the 9.75 mm gap |

Each pass is regenerated from the previous one with `scripts/build_passN.py <in> <out>`
(needs `cadquery-ocp`, i.e. OpenCascade 7.8).

* `asm_edit.py` - edit the assembly keeping part names, colours and placements
* `heal.py` - close open shells with exact flat faces (any number of planes, triangulation fallback)
* `geo270.py`, `geo012.py`, `geobase.py`, `geoarm.py`, `geocam.py` - part rebuilds
