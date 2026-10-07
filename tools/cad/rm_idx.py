import sys
exec(open("close_by_surface.py").read().split("s=rd(sys.argv[1])")[0])
s=rd(sys.argv[1]); drop=set(int(x) for x in sys.argv[3].split(",")); keep=[]; ex=TopExp_Explorer(s,TopAbs_FACE); i=0
while ex.More():
    if i not in drop: keep.append(ex.Current())
    i+=1; ex.Next()
sw=BRepBuilderAPI_Sewing(float(sys.argv[4]) if len(sys.argv)>4 else 0.003)
for f in keep: sw.Add(f)
sw.Perform(); BRepTools.Write_s(sw.SewedShape(),sys.argv[2]); print("removed",len(drop))
