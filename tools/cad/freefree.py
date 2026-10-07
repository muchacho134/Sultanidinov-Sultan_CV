import pickle, numpy as np, collections
from scipy.spatial import cKDTree
d=pickle.load(open("work/puzzle_pts.pkl","rb")); P,lab,isfree,info=d['P'],d['lab'],d['isfree'],d['info']
FP=P[isfree]; FL=lab[isfree]; tree=cKDTree(FP); STEP=0.1
res={}
for tol in (0.05,0.2,0.5,1.0):
    nb=tree.query_ball_point(FP,tol); W=collections.Counter()
    for i,cand in enumerate(nb):
        a=FL[i]
        for b in set(FL[j] for j in cand if FL[j]!=a): W[(a,b)]+=STEP
    res[tol]=W
    pairs={tuple(sorted(k)) for k,v in W.items() if v>=1.0}
    print(f"tol {tol}: pairs sharing >=1mm of free boundary: {len(pairs)}")
pickle.dump(res,open("work/freefree.pkl","wb"))
W=res[0.5]
rows=[]
for (a,b),L in W.items():
    if a<b:
        L2=W.get((b,a),0)
        if max(L,L2)>=1.0: rows.append((a,b,L,L2,info[a]['freelen'],info[b]['freelen']))
rows.sort(key=lambda r:-(r[2]+r[3]))
print("\nA, B, shared(on A), shared(on B), A total free, B total free   [tol 0.5]")
for r in rows[:60]: print("%-10s %-10s %7.1f %7.1f %8.1f %8.1f"%r)
