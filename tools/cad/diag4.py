exec(open("work/diag2.py").read().split("bore=BRepPrimAPI_MakeCylinder")[0])
for fz in [0.04,0.05,0.08,0.12]:
    t=cut(so,[upper],fz); ok=t is not None and V(t)
    if t is not None and not ok:
        sf=ShapeFix_Shape(t); sf.Perform(); t2=sf.Shape(); ok2=V(t2)
    else: ok2=ok; t2=t
    print("upper",fz,"valid",ok,"fixed",ok2,"removed %.1f"%(vol(so)-vol(t) if t is not None else -1),flush=True)
    if ok2: BRepTools.Write_s(t2,"work/d4_upper.brep"); break
