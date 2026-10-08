import json
exec(open("work/motorpos.py").read().split("docM,stM=load")[0])
T=[]
for i in range(1,cs.Length()+1):
    c=cs.Value(i); r_=TDF_Label(); stO.GetReferredShape_s(c,r_)
    if not stO.IsAssembly_s(r_): continue
    t=stO.GetLocation_s(c).Transformation(); tr=t.TranslationPart()
    m=[[t.Value(a,b) for b in (1,2,3)] for a in (1,2,3)]
    T.append({"name":nm(c),"o":[tr.X(),tr.Y(),tr.Z()],"x":[m[0][0],m[1][0],m[2][0]],"z":[m[0][2],m[1][2],m[2][2]]})
json.dump(T,open("work/motor_tf.json","w"),indent=1); print(len(T))
