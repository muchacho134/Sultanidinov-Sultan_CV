import sys; sys.argv=["x","/root/.claude/uploads/ee98767e-bf30-59cd-9d8f-10a3e03f94c6/a026cb78-Gun_solids_v6.step"]
exec(open("railpuzzle.py").read().split("for combo in")[0].replace("sys.argv[1]","'/root/.claude/uploads/ee98767e-bf30-59cd-9d8f-10a3e03f94c6/a026cb78-Gun_solids_v6.step'"))
sw=BRepBuilderAPI_Sewing(0.05); sw.Add(rail); sw.Add(parts['P267']); sw.Add(parts['P268']); sw.Perform()
sh=TopExp_Explorer(sw.SewedShape(),TopAbs_SHELL).Current()
BRepTools.Write_s(sh,"work/shell_a2.brep"); print("shell_a2 free loops:",loops(sh))
