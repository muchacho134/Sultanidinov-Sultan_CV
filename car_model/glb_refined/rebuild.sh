set -e
cd /tmp/claude-0/-home-user-Sultanidinov-Sultan-CV/1c61efcc-eff4-5e88-99f1-782388d9eb24/scratchpad
./venv/bin/python -u -I -W ignore glb_hull.py
./venv/bin/python -u -I -W ignore -c "
import trimesh, numpy as np, sys
sys.path.insert(0,'.')
from depthmap import depth_map
m=trimesh.load('out/glb_hull.stl'); m.merge_vertices()
cc=trimesh.graph.connected_components(m.face_adjacency, min_len=1); big=max(cc,key=len)
b=m.submesh([np.array(big)], append=True); b.merge_vertices()
trimesh.smoothing.filter_taubin(b, lamb=0.5, nu=-0.53, iterations=40)    # smooth the even mesh, then reduce
d=b.simplify_quadric_decimation(face_count=1500000); d.merge_vertices()
cc=trimesh.graph.connected_components(d.face_adjacency, min_len=1); big=max(cc,key=len)
d=d.submesh([np.array(big)], append=True); d.merge_vertices(); trimesh.repair.fix_normals(d)
u,c=np.unique(d.edges_sorted,axis=0,return_counts=True)
print('hull', len(d.faces), 'watertight', d.is_watertight, 'edge use', np.bincount(c)[:6], 'bounds', d.bounds.round(0).tolist())
d.export('out/glb_hull_dec.stl')
"
./venv/bin/python -u -I -W ignore pitfill.py out/glb_hull_dec.stl out/glb_hull_filled.stl
./venv/bin/python -u -I -W ignore -c "
import trimesh, numpy as np, sys
sys.path.insert(0,'.')
from depthmap import depth_map
d=trimesh.load('out/glb_hull_filled.stl')
ys,zs,Df=depth_map(d, 1, (-1000,1000), (0,1600), 4.0, 0.0); _,_,Dr=depth_map(d, -1, (-1000,1000), (0,1600), 4.0, 5360.0)
np.savez('out/hull_ends.npz', ysf=ys, zsf=zs, Ff=Df, ysr=ys, zsr=zs, Fr=Dr)
"
./venv/bin/python -u -I -W ignore glb_features.py 2>&1 | grep -v Warn
