exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
S=[("P223",'k'),("P214",'tab:green'),("P150",'tab:blue'),("P244",'tab:purple'),("P262",'tab:orange'),("P144",'tab:red'),("Barrel",'tab:brown'),("P256",'tab:cyan'),("P596",'tab:olive')]
S=[(n,c,rd(f"work/g_{n}.brep")) for n,c in S]
zs=[95,130,160,190,230,265]
fig,axs=plt.subplots(2,4,figsize=(36,20)); axs=axs.ravel(); px=lambda p:(p[0],p[1]); pz=lambda p:(p[2],p[1])
for i,z in enumerate(zs):
    ax=axs[i]
    for n,c,s in S: draw(ax,s,gp_Pln(gp_Pnt(0,0,z),gp_Dir(0,0,1)),px,c,n)
    h,l=ax.get_legend_handles_labels(); ax.legend(dict(zip(l,h)).values(),dict(zip(l,h)).keys(),fontsize=9)
    ax.set_title(f"z={z}",fontsize=20); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_xlim(-35,45); ax.set_ylim(-320,-200)
for j,x in enumerate([0.0,12.0]):
    ax=axs[6+j]
    for n,c,s in S: draw(ax,s,gp_Pln(gp_Pnt(x,0,0),gp_Dir(1,0,0)),pz,c,n)
    ax.set_title(f"x={x}",fontsize=20); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_xlim(60,300); ax.set_ylim(-320,-200)
plt.tight_layout(); plt.savefig("work/p223_secs.png",dpi=40); print("ok")
