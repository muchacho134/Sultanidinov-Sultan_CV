exec(open("front_build.py").read().split("Z0,ZC,ZR,ZE")[0])
S=rd("work/p223_solid_p.brep")
tools=[rd(f"work/{n}.brep") for n in ("g_P214","g_P256","g_P259","rs_solid")]
S=unify(cut(S,tools)); chk("carved",S); BRepTools.Write_s(S,"work/p223_solid.brep")
print("faces",count(S,TopAbs_FACE))
