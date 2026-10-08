exec(open("work/diag2.py").read().split("bore=BRepPrimAPI_MakeCylinder")[0])
s=rd("work/d4_upper.brep")
bore=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-267.9,245),gp_Dir(0,0,1)),12.7,296.63-245).Shape()
def step(s,tools,name):
    for fz in [0.0,0.005,0.02,0.08]:
        t=cut(s,tools,fz)
        if t is not None and not V(t): sf=ShapeFix_Shape(t); sf.Perform(); t=sf.Shape()
        if t is not None and V(t): print(name,"fz",fz,"removed %.1f"%(vol(s)-vol(t)),flush=True); return t
    print(name,"FAILED"); return s
s=step(s,prisms,"lug slab"); s=step(s,[bore],"bore")
s=step(s,[rd("work/closed_411.brep"),rd("work/closed_421.brep"),rd("work/closed_410.brep")],"pin/button/lever pockets")
BRepTools.Write_s(s,"work/p244_d5.brep"); print("valid",V(s),"faces",count(s,TopAbs_FACE),"solids",count(s,TopAbs_SOLID))
