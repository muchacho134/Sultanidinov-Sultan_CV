import pickle
res=pickle.load(open("work/freefree.pkl","rb")); d=pickle.load(open("work/puzzle_pts.pkl","rb")); info=d['info']
G=set("P165 P185 P186 P200 P202 P206 P207 P223 P227 P240 P244 P245 P251 P255 P258 P259 P261 P262 P264 P266 P267 P268 P592 P596 P597 P598".split())
print("pair            shared@0.05 shared@0.2 shared@0.5   %ofA  %ofB   freeA  freeB")
rows=[]
for (a,b),L in res[0.5].items():
    if a<b and a in G and b in G:
        s5=max(L,res[0.5].get((b,a),0)); s2=max(res[0.2].get((a,b),0),res[0.2].get((b,a),0)); s0=max(res[0.05].get((a,b),0),res[0.05].get((b,a),0))
        if s5<1: continue
        rows.append((a,b,s0,s2,s5,100*s5/info[a]['freelen'],100*s5/info[b]['freelen'],info[a]['freelen'],info[b]['freelen']))
for r in sorted(rows,key=lambda r:-r[4]): print("%-5s-%-5s %9.1f %10.1f %10.1f %6.0f %5.0f %7.0f %6.0f"%r)
for k in sorted(G): print(k,"solid" if info[k]['solid'] else "open", "free %.0f"%info[k]['freelen'])
