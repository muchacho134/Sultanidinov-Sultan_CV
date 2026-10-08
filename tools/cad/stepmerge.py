import re, sys, json
files=[("work/grouped_m_lean.step","Gun"),("work/addin/gunstruct.step","Gun_structure"),("work/addin/body_lean.step","Body_with_handles"),("work/addin/handle.step","Handle_all_solids"),("work/addin/motor.step","Motor")]
out=sys.argv[1]
ent_re=re.compile(r'(?m)^#(\d+)\s*=\s*')
def renum(txt,off):
    parts=txt.split("'"); 
    for i in range(0,len(parts),2): parts[i]=re.sub(r'#(\d+)',lambda m:'#%d'%(int(m.group(1))+off),parts[i])
    return "'".join(parts)
def entities(data):
    idx=[m for m in ent_re.finditer(data)]; E={}
    for k,m in enumerate(idx):
        end=idx[k+1].start() if k+1<len(idx) else len(data)
        body=data[m.end():end].strip()
        if body.endswith(";"): body=body[:-1]
        E[int(m.group(1))]=body
    return E
allE={}; off=0; roots=[]
for fn,label in files:
    txt=open(fn,encoding="latin-1").read()
    data=txt.split("DATA;",1)[1].rsplit("ENDSEC;",1)[0]
    E=entities(data)
    # root product definition: PRODUCT_DEFINITION not used as 'related' in any NAUO
    related=set(); 
    for i,b in E.items():
        if b.startswith("NEXT_ASSEMBLY_USAGE_OCCURRENCE"):
            refs=re.findall(r'#(\d+)',b); related.add(int(refs[1]))
    pds=[i for i,b in E.items() if b.startswith("PRODUCT_DEFINITION(") and i not in related]
    assert len(pds)==1,(fn,pds)
    pd=pds[0]
    pdss=[i for i,b in E.items() if b.startswith("PRODUCT_DEFINITION_SHAPE(") and re.findall(r'#(\d+)',b)[-1]==str(pd)]
    sdr=[b for i,b in E.items() if b.startswith("SHAPE_DEFINITION_REPRESENTATION(") and int(re.findall(r'#(\d+)',b)[0]) in pdss]
    sr=int(re.findall(r'#(\d+)',sdr[0])[1])
    srb=E[sr]; items=re.findall(r'#(\d+)',srb)
    ax=[int(x) for x in items if E.get(int(x),"").startswith("AXIS2_PLACEMENT_3D")]
    ctx=int(items[-1])
    print(fn,"root PD",pd,"SR",sr,"type",srb.split("(")[0],"axis",ax[:1],"entities",len(E))
    roots.append((label,pd+off,sr+off,(ax[0]+off) if ax else None,ctx+off,srb.split("(")[0]))
    for i,b in E.items(): allE[i+off]=renum(b,off)
    off=max(allE)+10
# new top assembly entities
n=[off]
def add(b): n[0]+=1; allE[n[0]]=b; return n[0]
ctx=roots[0][4]  # reuse gun's representation context (mm)
appctx=[i for i,b in allE.items() if b.startswith("APPLICATION_CONTEXT(")][0]
pctx=add("PRODUCT_CONTEXT('',#%d,'mechanical')"%appctx)
prod=add("PRODUCT('Gun_drone_full_assembly','Gun_drone_full_assembly','',(#%d))"%pctx)
pdf=add("PRODUCT_DEFINITION_FORMATION('','',#%d)"%prod)
pdctx=add("PRODUCT_DEFINITION_CONTEXT('part definition',#%d,'design')"%appctx)
pd=add("PRODUCT_DEFINITION('design','',#%d,#%d)"%(pdf,pdctx))
pds=add("PRODUCT_DEFINITION_SHAPE('','',#%d)"%pd)
o=add("CARTESIAN_POINT('',(0.,0.,0.))"); dz=add("DIRECTION('',(0.,0.,1.))"); dx=add("DIRECTION('',(1.,0.,0.))")
topax=add("AXIS2_PLACEMENT_3D('',#%d,#%d,#%d)"%(o,dz,dx))
TF=json.load(open("work/motor_tf.json"))
inst=[]   # (label, root tuple, placement)
for r in roots:
    if r[0]=="Motor":
        for k,t in enumerate(TF): inst.append(("Motor_%d"%(k+1),r,t))
    else: inst.append((r[0],r,{"o":[0,0,0],"x":[1,0,0],"z":[0,0,1]}))
f=lambda v:"(%s)"%",".join(repr(float(a)) for a in v)
childax=[]
for lab,r,t in inst:
    o2=add("CARTESIAN_POINT('',%s)"%f(t["o"])); z2=add("DIRECTION('',%s)"%f(t["z"])); x2=add("DIRECTION('',%s)"%f(t["x"]))
    childax.append(add("AXIS2_PLACEMENT_3D('',#%d,#%d,#%d)"%(o2,z2,x2)))
topsr=add("SHAPE_REPRESENTATION('',(#%s),#%d)"%(",#".join(str(x) for x in [topax]+childax),ctx))
add("SHAPE_DEFINITION_REPRESENTATION(#%d,#%d)"%(pds,topsr))
prc=[i for i,b in allE.items() if b.startswith("PRODUCT_RELATED_PRODUCT_CATEGORY(") or b.startswith("PRODUCT_CATEGORY(")]
for k,(label,r,t) in enumerate(inst):
    _,cpd,csr,cax,cctx,srt=r
    nauo=add("NEXT_ASSEMBLY_USAGE_OCCURRENCE('%d','%s','',#%d,#%d,$)"%(k+1,label,pd,cpd))
    npds=add("PRODUCT_DEFINITION_SHAPE('Placement','Placement of an item',#%d)"%nauo)
    idt=add("ITEM_DEFINED_TRANSFORMATION('','',#%d,#%d)"%(cax if cax else childax[k],childax[k]))
    rr=add("( REPRESENTATION_RELATIONSHIP('','',#%d,#%d) REPRESENTATION_RELATIONSHIP_WITH_TRANSFORMATION(#%d) SHAPE_REPRESENTATION_RELATIONSHIP() )"%(csr,topsr,idt))
    add("CONTEXT_DEPENDENT_SHAPE_REPRESENTATION(#%d,#%d)"%(rr,npds))
hdr=open(files[0][0],encoding="latin-1").read().split("DATA;",1)[0]
with open(out,"w",encoding="latin-1") as f:
    f.write(hdr+"DATA;\n")
    for i in sorted(allE): f.write("#%d = %s;\n"%(i,allE[i]))
    f.write("ENDSEC;\nEND-ISO-10303-21;\n")
print("written",out,"entities",len(allE))
