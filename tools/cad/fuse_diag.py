import glob, os, itertools
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common
from OCP.BRepExtrema import BRepExtrema_DistShapeShape
from OCP.Bnd import Bnd_Box; from OCP.BRepBndLib import BRepBndLib
from OCP.TopAbs import TopAbs_SOLID
P={os.path.basename(f)[:-5]:rd(f) for f in sorted(glob.glob("work/gunp/*.brep"))}
names=list(P)
def bb(s,e=0):
    b=Bnd_Box(); BRepBndLib.Add_s(s,b); b.Enlarge(e); return b
B={k:bb(v,0.5) for k,v in P.items()}
touch={k:set() for k in names}; over=[]
for a,b in itertools.combinations(names,2):
    if B[a].IsOut(B[b]): continue
    d=BRepExtrema_DistShapeShape(P[a],P[b]); d.Perform()
    if d.Value()<=0.01:
        touch[a].add(b); touch[b].add(a)
        v=vol(BRepAlgoAPI_Common(P[a],P[b]).Shape())
        if v>0.5: over.append((round(v,1),a,b))
# connected components
seen=set(); comps=[]
for k in names:
    if k in seen: continue
    st=[k]; c=[]
    while st:
        x=st.pop()
        if x in seen: continue
        seen.add(x); c.append(x); st+=list(touch[x])
    comps.append(sorted(c))
comps.sort(key=len,reverse=True)
print("connected groups (parts touching within 0.01 mm):",len(comps))
for c in comps: print("  ",len(c),"parts:",", ".join(c))
print("\noverlapping pairs (>0.5 mm3):",len(over))
for v,a,b in sorted(over,reverse=True): print("   %8.1f  %s  x  %s"%(v,a,b))
# nearest gap for isolated groups
if len(comps)>1:
    main=comps[0]
    for c in comps[1:]:
        best=None
        for a in c:
            for b in main:
                d=BRepExtrema_DistShapeShape(P[a],P[b]); d.Perform()
                if best is None or d.Value()<best[0]: best=(d.Value(),a,b)
        print("group",c,"-> nearest to main body: %.3f mm (%s to %s)"%best)
