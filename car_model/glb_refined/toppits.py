import sys; sys.path.insert(0,'.')
import trimesh, numpy as np
from scipy import ndimage
from depthmap import depth_map
m=trimesh.load(sys.argv[1])
mt=trimesh.Trimesh(m.vertices[:,[2,0,1]],m.faces,process=False)
xs,ys,D=depth_map(mt,-1,(0,5360),(-1000,1000),4.0,1800.0)
h=1800-D; v=np.isfinite(h); hn=np.where(v,h,0)
pit=ndimage.grey_closing(hn,size=(9,9))-hn
g=np.hypot(*np.gradient(hn,4.0))
lab,n=ndimage.label((pit>2)&ndimage.binary_erosion(v,iterations=4)&(g<1.0))
out=[]
for sl in ndimage.find_objects(lab):
  r=pit[sl]; i=np.unravel_index(np.argmax(r),r.shape)
  out.append((r.max(), xs[sl[1].start+i[1]], ys[sl[0].start+i[0]]))
print(len(out),'top pits >2mm;', ' '.join('(%d,%d %.0fmm)'%(x,y,d) for d,x,y in sorted(out)[::-1][:25]))
