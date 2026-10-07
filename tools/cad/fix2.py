exec(open("rs_build.py").read().split("G={}")[0])
Y,Z=-243.90,0
B=rd("work/g_Barrel.brep"); P=rd("work/g_P150.brep"); K=rd("work/g_P214.brep")
def zcyl(r,z0,z1): return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,Y,z0),gp_Dir(0,0,1)),r,z1-z0).Shape()
# gas cylinder + piston rod, rod stops at the carrier cup face z=121.87
gas=common(B,box(-20,-260,-300,20,-225,121.87)); gas=unify(gas); chk("Gas_Cylinder",gas)
# spring envelope (solid_153, R4 z136.29-285.29) merged with guide rod/charging part P150
spr=common(B,box(-20,-260,136.0,20,-225,300)); chk("spring",spr)
rod=unify(fuse([P,spr])); chk("P150+spring",rod)
# carrier: R4 bore at the back of its cup for the rod/spring front end
K2=unify(cut(K,[zcyl(4.05,135.9,160.5)])); chk("P214",K2)
for n,a,b in [("gas&P150",gas,rod),("gas&P214",gas,K2),("P214&P150",K2,rod)]: print(n,"overlap",round(vol(common(a,b)),3))
BRepTools.Write_s(gas,"work/gas_solid.brep"); BRepTools.Write_s(rod,"work/p150_spring.brep"); BRepTools.Write_s(K2,"work/p214_bored.brep")
