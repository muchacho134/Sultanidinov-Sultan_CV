exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
S=rd("work/g_P244.brep"); U=rd("work/p223_final.brep"); M=rd("work/g_P256.brep"); L=rd("work/g_P259.brep"); H=rd("work/g_P596.brep")
fig,axs=plt.subplots(2,4,figsize=(36,18)); axs=axs.ravel(); px=lambda p:(p[0],p[1]); pz=lambda p:(p[2],p[1])
for ax,(k,v) in zip(axs,[("z",120),("z",150),("z",185),("z",220),("z",250),("z",285),("x",0.0),("x",-11.0)]):
    pl=gp_Pln(gp_Pnt(0,0,v),gp_Dir(0,0,1)) if k=="z" else gp_Pln(gp_Pnt(v,0,0),gp_Dir(1,0,0)); pr=px if k=="z" else pz
    draw(ax,S,pl,pr,'k',"P244"); draw(ax,U,pl,pr,'tab:gray',"P223"); draw(ax,M,pl,pr,'tab:cyan',"mag"); draw(ax,L,pl,pr,'tab:red',"P259"); draw(ax,H,pl,pr,'tab:olive',"P596")
    h,l=ax.get_legend_handles_labels(); ax.legend(dict(zip(l,h)).values(),dict(zip(l,h)).keys(),fontsize=9)
    ax.set_title(f"{k}={v}",fontsize=18); ax.set_aspect('equal'); ax.grid(alpha=.3)
    if k=="z": ax.set_xlim(-30,30); ax.set_ylim(-340,-225)
    else: ax.set_xlim(85,325); ax.set_ylim(-340,-225)
plt.tight_layout(); plt.savefig("work/p244_secs.png",dpi=40); print("ok")
