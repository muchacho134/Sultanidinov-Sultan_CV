exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
O=rd("work/o_P262.brep"); N=rd("work/g_P262.brep"); C=rd("work/g_P223.brep"); B=rd("work/g_Barrel.brep"); T=rd("work/g_P213.brep")
fig,axs=plt.subplots(1,5,figsize=(40,9)); px=lambda p:(p[0],p[1])
for ax,z in zip(axs,(-100,0,60,130,200)):
    pl=gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1))
    draw(ax,N,pl,px,'tab:orange',"rail now"); draw(ax,O,pl,px,'k',"rail original shell"); draw(ax,C,pl,px,'tab:gray',"P223"); draw(ax,B,pl,px,'tab:brown',"Barrel"); draw(ax,T,pl,px,'tab:blue',"P213")
    h,l=ax.get_legend_handles_labels(); ax.legend(dict(zip(l,h)).values(),dict(zip(l,h)).keys()); ax.set_title(f"z={z}",fontsize=20); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_xlim(-32,32); ax.set_ylim(-300,-215)
plt.tight_layout(); plt.savefig("work/rail_cmp.png",dpi=40); print("ok")
