"""Yoke arm cluster and small loose pieces.

* 083 (arm): open shell closed with exact flat faces (heal.close); the tiny
  countersink seat under screw 079 is capped flat.  The clamp blocks 080 / 081
  and the top cap 066 were loose surface fragments sitting on the arm: they
  are rebuilt as solid blocks with their counterbored holes (081's hole had
  been capped) and kept as separate solids of the arm part.
* 097 (slider channel): closed with exact flat faces; its countersink seat is
  capped flat under the screw head.
* screws / nuts that were stored as loose thread and head surfaces are
  replaced by plain solids (shank + head) on the same axis.
"""
import math
from geo270 import fuse, cut, fuse_many, cut_many, box
from OCP.gp import gp_Pnt, gp_Dir, gp_Ax2
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder
from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing
import heal


def cyl(p, d, r, h):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(*p), gp_Dir(*d)), r, h).Shape()


def ring(p, d, r_out, r_in, h):
    return cut(cyl(p, d, r_out, h), cyl(p, d, r_in, h))


def close_part(shape, drop=None, tol=0.02):
    if drop:
        shape, _ = heal.drop_faces(shape, drop)
    so, rep = heal.close(shape, tol=tol, fill_rest=True)
    assert so is not None and rep['valid'] and rep['volume'] > 0, rep
    return so


def build_arm(parts):
    arm = close_part(parts['083'], drop=(17.5, -201.2, 41.5, 18.2, -197.0, 46.5))
    # clamp blocks on the -X rail, each with a counterbored hole along X
    blocks, holes = [], []
    for (y0, y1, z0, z1, zc) in ((-211.1, -195.1, 70.0, 85.0, 77.5), (-211.1, -198.6, 17.0, 32.0, 24.5)):
        blocks.append(box(-15.41, y0, z0, -11.41, y1, z1))
        holes += [cyl((-15.5, -202.6, zc), (1, 0, 0), 3.0, 1.09), cyl((-15.5, -202.6, zc), (1, 0, 0), 1.75, 4.2)]
    # top cap 066 with two counterbored holes along Y
    blocks.append(box(-9.41, -200.1, 78.98, 10.59, -194.1, 91.0))
    for x in (-5.91, 7.09):
        holes += [cyl((x, -194.0, 85.0), (0, -1, 0), 3.25, 3.6), cyl((x, -194.0, 85.0), (0, -1, 0), 1.75, 6.2)]
    # booleans against the patched arm are unreliable, so the blocks stay separate
    # solids of the same part (they sit on the arm's rail / top notch)
    from asm_edit import compound
    return compound([arm] + [cut_many(b, holes) for b in blocks])


def build_slider(parts):
    shell, _ = heal.drop_faces(parts['097'], (-2.7, -186.6, 62.9, 3.9, -185.0, 66.3))   # countersink seat
    return close_part(shell, drop=(2.9, -188.7, 48.4, 5.7, -185.0, 51.8))                  # small hole entry


def build_fasteners():
    f = {}
    # screws through the yaw-housing panel (001/002 pattern; 003 only had its end)
    for key, (y, z) in (('001', (-197.53, -38.90)), ('002', (-105.53, -3.90)), ('003', (-197.53, -3.90))):
        f[key] = fuse(cyl((-73.59, y, z), (1, 0, 0), 1.35, 14.8), cyl((-75.59, y, z), (1, 0, 0), 3.0, 2.0))
    # pins in the ring disc (004 at Z=-6; 008 was only the end of its twin at Z=+6)
    for key, z in (('004', -6.0), ('008', 6.0)):
        f[key] = cyl((-88.19, -265.4, z), (1, 0, 0), 0.8, 3.0)
    # clip ring on the second rod
    f['019'] = ring((-34.0, -237.4, 27.6), (0, 0, 1), 6.8, 4.0, 1.11)
    # screw with washer at the arm foot (067-070, 104, 106)
    # (washer face flush with the arm's back face, as in the original)
    f['070'] = fuse_many([cyl((0.59, -206.1, -37.0), (0, 1, 0), 1.75, 9.0),
                          cyl((0.59, -206.1, -37.0), (0, 1, 0), 5.0, 0.5),
                          cyl((0.59, -206.1, -37.0), (0, 1, 0), 3.0, 2.0)])
    # pivot screw at the arm top (071-076)
    f['076'] = fuse(cyl((0.59, -185.1, 63.0), (0, -1, 0), 1.4, 6.0), cyl((0.59, -186.3, 63.0), (0, 1, 0), 3.0, 1.2))
    # countersunk screw in the arm's +X face (077-079) and its neighbour (101, 107, 108)
    f['079'] = cyl((14.4, -199.1, 44.0), (1, 0, 0), 1.86, 3.69)
    f['101'] = cyl((16.8, -199.1, 52.0), (1, 0, 0), 1.0, 1.29)
    # set screw in the slider (084-096)
    f['086'] = cyl((-1.41, -200.1, 47.95), (0, 1, 0), 1.5, 4.7)
    # pin inside the right pivot boss
    f['064'] = cyl((7.0, -199.1, 63.0), (1, 0, 0), 3.0, 9.0)
    return f


# fragments that are superseded (faces of rebuilt parts, caps, loose thread pieces)
DROP = ['005', '006', '007', '009', '013', '066', '067', '068', '069', '071', '072', '074', '075', '077', '078',
        '080', '081', '082', '084', '085', '087', '088', '089', '090', '091', '092', '093', '094', '095', '096',
        '098', '099', '100', '103', '104', '105', '106', '107', '108', '271']
