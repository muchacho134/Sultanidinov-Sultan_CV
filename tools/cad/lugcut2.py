exec(open("work/pipeline244.py").read().split("s=rd(sys.argv[1]); ex=TopExp_Explorer")[0])
so=rd("work/p244_pre223.brep"); P=rd("work/cur_P223.brep")
for z0 in [256.3,256.5]:
  for fz in [0.0,0.001,0.005]:
    box=BRepPrimAPI_MakeBox(gp_Pnt(-25,-283.5,z0),gp_Pnt(25,-235,300)).Shape()
    tl=BRepAlgoAPI_Common(P,box).Shape(); t=cut(so,[tl],fz); ok=t is not None and V(t)
    print(z0,fz,"tool %.1f"%vol(tl),"valid",ok,"vol %.1f"%(vol(t) if t is not None else 0))
    if ok: BRepTools.Write_s(t,"work/p244_lug.brep"); raise SystemExit
