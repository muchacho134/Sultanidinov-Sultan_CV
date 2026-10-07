exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
S=rd("work/p244_ck5.brep"); U=rd("work/p223_final.brep")
fb=ShapeAnalysis_FreeBounds(S,1e-4); ex=TopExp_Explorer(fb.GetClosedWires(),TopAbs_EDGE); FP=[]
while ex.More():
    c=BRepAdaptor_Curve(TopoDS.Edge_s(ex.Current())); d=GCPnts_QuasiUniformDeflection(c,0.05)
    FP+=[(d.Value(k).X(),d.Value(k).Y(),d.Value(k).Z()) for k in range(1,d.NbPoints()+1)]; ex.Next()
FP=np.array(FP)
fig,axs=plt.subplots(2,4,figsize=(36,18)); axs=axs.ravel(); px=lambda p:(p[0],p[1]); pz=lambda p:(p[2],p[1])
for ax,(k,v) in zip(axs,[("z",172),("z",185),("z",200),("z",240),("z",262),("z",280),("z",293),("x",-11.0)]):
    pl=gp_Pln(gp_Pnt(0,0,v),gp_Dir(0,0,1)) if k=="z" else gp_Pln(gp_Pnt(v,0,0),gp_Dir(1,0,0)); pr=px if k=="z" else pz
    draw(ax,S,pl,pr,'k',"P244"); draw(ax,U,pl,pr,'tab:gray',"P223")
    ax_i=2 if k=="z" else 0
    m=np.abs(FP[:,ax_i]-v)<1.0
    if m.any(): P=FP[m]; Q=np.array([pr(p) for p in P]); ax.plot(Q[:,0],Q[:,1],'r.',ms=4,label="open edge pts (±1mm)")
    h,l=ax.get_legend_handles_labels(); ax.legend(dict(zip(l,h)).values(),dict(zip(l,h)).keys(),fontsize=9)
    ax.set_title(f"{k}={v}",fontsize=18); ax.set_aspect('equal'); ax.grid(alpha=.3)
    if k=="z": ax.set_xlim(-28,28); ax.set_ylim(-340,-225)
    else: ax.set_xlim(160,305); ax.set_ylim(-340,-225)
plt.tight_layout(); plt.savefig("work/big_secs.png",dpi=40); print("ok")
