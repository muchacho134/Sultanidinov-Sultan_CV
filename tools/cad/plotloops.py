import sys, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
exec(open("lids.py").read().split("def lid_pass")[0].replace("src,out_brep,out_step,tol=sys.argv[1],sys.argv[2],sys.argv[3],float(sys.argv[4])","src,out_brep,out_step,tol='work/shell_a.brep','x','y',0.05"))
W=wires(shell)
fig,ax=plt.subplots(3,1,figsize=(18,12))
cols={2:'tab:red',3:'tab:blue'}
for i in (2,3):
    P=ordered_points(W[i],0.1)
    ax[0].plot(P[:,2],P[:,0],'-',c=cols[i],lw=1,label=f"loop {i}"); ax[0].set_xlabel("z"); ax[0].set_ylabel("x")
    ax[1].plot(P[:,2],P[:,1],'-',c=cols[i],lw=1); ax[1].set_xlabel("z"); ax[1].set_ylabel("y (height)")
    ax[2].plot(P[:,0],P[:,1],'.',c=cols[i],ms=2); ax[2].set_xlabel("x"); ax[2].set_ylabel("y")
ax[0].legend(); ax[0].set_xlim(-220,200); ax[1].set_xlim(-220,200); ax[2].set_aspect('equal')
plt.tight_layout(); plt.savefig("work/loops23.png",dpi=55); print("ok")
