exec(open("p110_sec.py").read().split("A=rd(")[0])
exec("def draw"+open("p110_sec.py").read().split("def draw")[1].split("pz=lambda")[0])
S=rd("work/x_P596.brep"); T=rd("work/x_P593.brep")
br=[-68.2,-66.7,-65.2,-55.7,-54.2,-32.5,-24.5,-15.7,-14.5,-14.2,-11.7,-10.7,-10.2,-5.5,2.5,5.5,5.7,9.4,11.7,12.7,14.7,15.7]
mids=[(a+b)/2 for a,b in zip(br[:-1],br[1:])]
fig,axs=plt.subplots(4,6,figsize=(42,26)); axs=axs.ravel()
pz=lambda p:(p[2],p[1])
for i,x in enumerate(mids):
    ax=axs[i]; draw(ax,S,gp_Pln(gp_Pnt(x,0,0),gp_Dir(1,0,0)),pz,'k',None); draw(ax,T,gp_Pln(gp_Pnt(x,0,0),gp_Dir(1,0,0)),pz,'tab:orange',None)
    ax.set_title(f"x={x:.2f}",fontsize=20); ax.set_aspect('equal'); ax.grid(alpha=.4); ax.set_xlim(165,290); ax.set_ylim(-350,-270)
    ax.set_xticks(range(170,291,10)); ax.set_yticks(range(-350,-269,10))
plt.tight_layout(); plt.savefig("work/p596_slabs.png",dpi=40); print(len(mids))
