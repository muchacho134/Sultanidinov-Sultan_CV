exec(open("close5.py").read().split("fb=ShapeAnalysis_FreeBounds(s,1e-4); ex=")[0])
sw=BRepBuilderAPI_Sewing(1e-4)
for f,_ in faces: sw.Add(f)
sw.Perform(); print("resewn original valid-check:",BRepAlgoAPI_Check(sw.SewedShape(),True,True).IsValid())
