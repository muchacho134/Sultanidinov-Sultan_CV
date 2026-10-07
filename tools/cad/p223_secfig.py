exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
N=rd("work/p223_final.brep"); O=rd("work/g_P223.brep")
fig,axs=plt.subplots(1,4,figsize=(36,9)); px=lambda p:(p[0],p[1]); pz=lambda p:(p[2],p[1])
for ax,(k,v) in zip(axs,[("z",80),("z",150),("z",265),("x",0.0)]):
    pl=gp_Pln(gp_Pnt(0,0,v),gp_Dir(0,0,1)) if k=="z" else gp_Pln(gp_Pnt(v,0,0),gp_Dir(1,0,0)); pr=px if k=="z" else pz
    draw(ax,O,pl,pr,'tab:red',"original P223"); draw(ax,N,pl,pr,'k',"closed solid")
    h,l=ax.get_legend_handles_labels(); ax.legend(dict(zip(l,h)).values(),dict(zip(l,h)).keys())
    ax.set_title(f"{k}={v}",fontsize=18); ax.set_aspect('equal'); ax.grid(alpha=.3)
    if k=="x": ax.set_xlim(65,300); ax.set_ylim(-300,-200)
    else: ax.set_xlim(-22,22); ax.set_ylim(-300,-200)
plt.tight_layout(); plt.savefig("work/p223_secs.png",dpi=45)
