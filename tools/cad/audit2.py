import sys
exec(open("work/audit.py").read().split("for n,s in out:")[0])
from OCP.BRepCheck import BRepCheck_Analyzer
bad=0
for n,s in out:
    ns=count(s,TopAbs_SOLID); fb=ShapeAnalysis_FreeBounds(s,1e-3); fe=count(fb.GetClosedWires(),TopAbs_EDGE)+count(fb.GetOpenWires(),TopAbs_EDGE)
    v=BRepCheck_Analyzer(s).IsValid(); k=n.replace("조준경 + 짐벌 + 소총","P")
    ok= ns==1 and fe==0 and v and vol(s)>0
    bad+= not ok
    print("%-14s %-32s solids %d freeEdges %3d valid %-5s vol %10.1f %s"%(k,grp.get(n,"?"),ns,fe,v,vol(s) if ns else 0,"" if ok else "  <-- PROBLEM"))
print("parts",len(out),"problems",bad)
