exec(open("work/pipeline244.py").read().split("s=rd(sys.argv[1]); ex=TopExp_Explorer")[0])
so=rd("work/p244_lug.brep")
for y0 in [-283.1,-283.12,-283.09]:
  for fz in [0.0,0.001,0.005]:
    b=BRepPrimAPI_MakeBox(gp_Pnt(-12.65,y0,256.0),gp_Pnt(12.85,-282.5,256.6)).Shape()
    t=cut(so,[b],fz); ok=t is not None and V(t)
    print(y0,fz,ok,"faces",count(t,TopAbs_FACE) if t is not None else 0)
    if ok: BRepTools.Write_s(t,"work/p244_slab_%g_%g.brep"%(y0,fz))
