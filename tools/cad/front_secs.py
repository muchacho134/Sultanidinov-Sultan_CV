exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
S=rd("work/p223_ckpt3.brep"); K=rd("work/g_P214.brep"); R=rd("work/g_P262.brep"); G=rd("work/gas_solid.brep"); T=rd("work/g_P213.brep")
fig,axs=plt.subplots(2,4,figsize=(36,18)); axs=axs.ravel(); px=lambda p:(p[0],p[1]); pz=lambda p:(p[2],p[1])
for ax,(k,v) in zip(axs,[("z",69.9),("z",72),("z",80),("z",89.8),("z",92),("x",0.0),("x",5.0),("x",12.0)]):
    pl=gp_Pln(gp_Pnt(0,0,v),gp_Dir(0,0,1)) if k=="z" else gp_Pln(gp_Pnt(v,0,0),gp_Dir(1,0,0)); pr=px if k=="z" else pz
    draw(ax,S,pl,pr,'k',"P223"); draw(ax,K,pl,pr,'tab:green',"P214"); draw(ax,R,pl,pr,'tab:orange',"rail"); draw(ax,G,pl,pr,'tab:brown',"gas"); draw(ax,T,pl,pr,'tab:blue',"P213")
    free(ax,S,pr)
    h,l=ax.get_legend_handles_labels(); ax.legend(dict(zip(l,h)).values(),dict(zip(l,h)).keys(),fontsize=9)
    ax.set_title(f"{k}={v}",fontsize=18); ax.set_aspect('equal'); ax.grid(alpha=.3)
    if k=="z": ax.set_xlim(-25,25); ax.set_ylim(-300,-225)
    else: ax.set_xlim(55,115); ax.set_ylim(-300,-225)
plt.tight_layout(); plt.savefig("work/front_secs.png",dpi=40); print("ok")
