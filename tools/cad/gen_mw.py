import json, sys
exec(open("split_fill.py").read().split("new=[]")[0].replace("spec=json.loads(open(sys.argv[3]).read())","spec=[]"))
near=[-0.66,-308.23,135.08]; YM=-283.3
L=min(loops,key=lambda l:(l[0]-near[0])**2+(l[1]-near[1])**2+(l[2]-near[2])**2); E=L[3]
print("edges",len(E))
pairs=[([13],[35]),([12],[36]),([11],[37]),([10],[38]),([9],[39]),([8],[40]),([5,6,7],[41,42]),
       ([14],[32,33,34]),
       ([15],[31]),([16],[30]),([17],[29]),([18],[28]),([19],[26,27])]
groups=[]
for T,B in pairs:
    bv=[ends(E[B[0]])[0]]+[ends(E[j])[1] for j in B]          # bottom vertices in loop order
    M=[["p",round(p.X(),5),YM,round(p.Z(),5)] for p in bv]
    groups.append({"e":B+M[::-1],"plane":"auto"})             # vertical wall
    groups.append(T+M)                                         # chamfer strip (top edges then M from near-end)
groups += [[4,43,0],[1,2,3],[20,24,25],[21,22,23]]
json.dump([{"near":near,"explicit":1,"groups":groups}],open("work/mw2.json","w"))
print("groups",len(groups))
