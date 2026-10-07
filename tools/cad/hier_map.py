import pickle, numpy as np, collections
rows=pickle.load(open("work/overview.pkl","rb"))
def grp(r):
    n=r['short']; b=r['bbox']; c=(b[:3]+b[3:])/2; d=b[3:]-b[:3]
    if c[2]<-330: return "01_Muzzle"
    if n in ("solid_109","solid_599","solid_600","solid_601"): return "02_Mount_Plates"
    if n in ("solid_228","solid_229","solid_219"): return "03_Front_Bracket"
    if n in ("P262","P263","P265","P264","P225","P269","P214","P218","P213","P160","P224","P170"): return "04_Rail_Handguard"
    if n in ("P110","P111","solid_127","solid_131","P112","P113"): return "06_Front_Sight_Barrel_Fittings"
    if abs(c[0])<1.5 and abs(c[1]+244)<3 and c[2]<95: 
        return "05_Barrel" if d[2]>50 else "06_Front_Sight_Barrel_Fittings"
    if n=="P256": return "10_Magazine"
    if n in ("P596","P593","P594","P595"): return "11_Side_Housing"
    if n=="P223" or n in ("P150","P151","P154"): return "07_Upper_Receiver"
    if c[2]>225 and c[1]>-232: return "08_Rear_Sight_Top"
    if n=="P244": return "09_Lower_Receiver"
    if n in ("P259","P250","solid_252","solid_253","P257","P260","P245","P248","solid_249","P258","P247","P246","P254","P255"): return "09_Lower_Receiver"
    if 90<c[2]<215 and -280<c[1]<-240: return "12_Bolt_Carrier_Internals"
    if abs(c[0])<1.5 and abs(c[1]+244)<3: return "12_Bolt_Carrier_Internals"
    return "99_Unsorted"
G=collections.defaultdict(list)
for r in rows: G[grp(r)].append(r['short'])
for g in sorted(G): print(f"{g} ({len(G[g])}): "+", ".join(sorted(G[g])))
pickle.dump({r['name']:grp(r) for r in rows},open("work/hier_map.pkl","wb"))
