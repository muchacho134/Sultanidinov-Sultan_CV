exec(open("front_build.py").read().split("Z0,ZC,ZR,ZE")[0])
S=rd("work/p223_solid_raw.brep")
S=cut(S,[zc(YB,12.7,69.0,103.7), zc(YC,8.9,69.0,78.9), zc(YC,2.6,78.0,112.0)])
S=unify(S); chk("with passages",S); BRepTools.Write_s(S,"work/p223_solid_p.brep")
