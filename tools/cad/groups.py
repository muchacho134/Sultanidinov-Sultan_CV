import pickle, collections
g=pickle.load(open("work/puzzle_graph.pkl","rb")); W=g['W']; info=g['info']
# symmetric link strength: matched length on each side
links={}
for (a,b),L in W.items():
    key=tuple(sorted((a,b))); links.setdefault(key,[0,0]); links[key][0 if key[0]==a else 1]+=L
strong={k:v for k,v in links.items() if max(v)>=1.0}
print("links total",len(links),"strong (>=1mm shared)",len(strong))
# union-find
par={}
def f(x):
    par.setdefault(x,x)
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
for a,b in strong: par[f(a)]=f(b)
comp=collections.defaultdict(list)
for k in info:
    if info[k]['nfree']>0 or any(k in s for s in strong): comp[f(k)].append(k)
groups=[sorted(v) for v in comp.values() if len(v)>1]
singles=[v[0] for v in comp.values() if len(v)==1]
groups.sort(key=len,reverse=True)
print("multi-part groups:",len(groups)," open parts with no partner:",len(singles))
for gi,G in enumerate(groups):
    print(f"G{gi} ({len(G)}):",", ".join(G[:40]) + (" ..." if len(G)>40 else ""))
pickle.dump(dict(groups=groups,singles=singles,strong=strong),open("work/groups.pkl","wb"))
