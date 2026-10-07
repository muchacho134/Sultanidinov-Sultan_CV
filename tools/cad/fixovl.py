exec(open("work/pipeline244.py").read().split("s=rd(sys.argv[1]); ex=TopExp_Explorer")[0])
def best_cut(a,tools,name):
    for fz in [0.005,0.001,0.0,0.01]:
        t=cut(a,tools,fz)
        if t is not None and not V(t): sf=ShapeFix_Shape(t); sf.Perform(); t=sf.Shape()
        if t is not None and V(t):
            print(name,"fz",fz,"vol %.1f -> %.1f"%(vol(a),vol(t))); return t
    print(name,"FAILED"); return a
p=best_cut(rd("work/p244_c3.brep"),[rd("work/closed_411.brep"),rd("work/closed_421.brep"),rd("work/closed_410.brep")],"P244"); BRepTools.Write_s(p,"work/p244_c4.brep")
for n,par in [("388","work/rail_in/rail.brep"),("417","work/allp/P596.brep"),("432","work/allp/P223.brep")]:
    t=best_cut(rd(f"work/closed_{n}.brep"),[rd(par)],n); BRepTools.Write_s(t,f"work/closed_{n}c.brep")
