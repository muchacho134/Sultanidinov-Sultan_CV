exec(open('build.py').read().split("print('args',len(args))")[0])
zs=[float(v) for v in sys.argv[2].split(',')]
extra=[face_pts((-40,-300,z),(40,-300,z),(40,-200,z),(-40,-200,z)) for z in zs]
mv=BOPAlgo_MakerVolume(); L=TopTools_ListOfShape()
for a in args+extra: L.Append(a)
mv.SetArguments(L); mv.SetFuzzyValue(FZ); mv.SetRunParallel(True); mv.Perform()
cells=[]; e=TopExp_Explorer(mv.Shape(),TopAbs_SOLID)
while e.More(): cells.append(e.Current()); e.Next()
ccl=BRepClass3d_SolidClassifier(cav)
import collections
by=collections.defaultdict(float)
for c in cells:
    b=bb(c); g=GProp_GProps(); BRepGProp.VolumeProperties_s(c,g); p=g.CentreOfMass()
    ccl.Perform(p,1e-7)
    if ccl.State()==TopAbs_IN: continue
    by[round(p.Z())]+=0
    print('cell v=%.1f'%vol(c), [round(v,1) for v in b])
