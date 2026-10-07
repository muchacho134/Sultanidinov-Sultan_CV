exec(open("hous_build.py").read().split("# ---- box profile")[0])
A=lambda cz,cy:('A',(cz,cy))
from OCP.BRepPrimAPI import BRepPrimAPI_MakeCone
from OCP.gp import gp_Ax1
import math
def xcyl(y,z,r,x0,x1): return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x0,y,z),gp_Dir(1,0,0)),r,x1-x0).Shape()
def xcone(y,z,r0,r1,x0,x1):
    if x1>x0: return BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(x0,y,z),gp_Dir(1,0,0)),r0,r1,x1-x0).Shape()
    return BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(x0,y,z),gp_Dir(-1,0,0)),r0,r1,x0-x1).Shape()
def ycyl(x,z,r,y0,y1,d=(0,1,0)):
    return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x,y0,z),gp_Dir(*d)),r,y1-y0).Shape()
def rotx(s,ang,pt):
    t=gp_Trsf(); t.SetRotation(gp_Ax1(pt,gp_Dir(1,0,0)),ang)
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    return BRepBuilderAPI_Transform(s,t,True).Shape()
G={}
# ---------- P144 bracket: side profile (z,y) extruded over x +-4.65
PR=[(225.99,-221.46),(227.57,-221.70),(227.73,-220.66),(235.47,-220.72),A(239.19,-220.20),(239.46,-223.94),(249.19,-223.23),(258.12,-219.16),
    A(260.02,-219.79),(259.87,-217.79),A(260.02,-219.79),(260.29,-217.81),(264.29,-218.36),(265.85,-207.0),(263.32,-207.0),(262.48,-213.14),
    A(260.50,-212.87),(260.64,-214.87),(228.21,-217.25),A(228.35,-219.24),(226.38,-218.93),(225.99,-221.46)]
br=prism(face(PR),-4.65,4.65)
br=fuse([br,xcyl(-220.20,239.19,3.75,-8.15,8.15)])
# rounded tongue tip: R4.65 about tilted axis (0,-0.14,0.99) through (0,-212.01,258.11)
th=math.asin(0.14); O=gp_Pnt(0,-212.01,258.11); ad=(0,-0.1400,0.9902)
cutter=rotx(box(-6,0,-12,6,10,15),th,gp_Pnt(0,0,0)); t=gp_Trsf(); t.SetTranslation(gp_Vec(0,-212.01,258.11))
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
cutter=BRepBuilderAPI_Transform(cutter,t,True).Shape()
tcyl=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-212.01-ad[1]*15,258.11-ad[2]*15),gp_Dir(*ad)),4.65,40).Shape()
br=cut(br,[cut(cutter,[tcyl])])
# countersunk hole (countersink on the underside)
ap=(0,-212.90,264.63); dd=(0,0.14,-0.99); n=math.hypot(*dd); dd=(0,dd[1]/n,dd[2]/n)
hole=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,ap[1]-4*dd[1],ap[2]-4*dd[2]),gp_Dir(*dd)),0.9,9).Shape()
csk=BRepPrimAPI_MakeCone(gp_Ax2(gp_Pnt(0,ap[1]+0.9*dd[1],ap[2]+0.9*dd[2]),gp_Dir(*dd)),0.9,3.0,2.1).Shape()
# window and 9 serration grooves (pitch 0.9, width 0.4)
win=box(-1.5,-226,242.94,1.5,-210,258.70)
gro=[prism(face([(263.62,-219.5),(264.04,-216.5),(266.5,-216.5),(266.5,-219.5),(263.62,-219.5)]),-3.8+0.9*k,-3.4+0.9*k) for k in range(9)]
br=cut(br,[hole,csk,win]+gro); G["P144"]=chk("P144",br)
# ---------- P147 leaf spring on the back of the bracket (1.6 thick, R1.5 corners)
lf=prism(face([(227.04,-215.62),(245.29,-214.29),(245.41,-215.89),(227.16,-217.22),(227.04,-215.62)]),-5.55,5.55)
G["P147"]=chk("P147",fuse([lf,ycyl(0,236.52,2.4,-217.05,-215.8)]))
# ---------- pin + roller in the window, small bar P149
G["pin"]=chk("pin",xcyl(-216.76,256.72,0.8,-4.65,4.65))
G["P148"]=chk("P148",xcyl(-216.26,256.76,1.0,-2.45,2.45))
G["P149"]=chk("P149",fuse([box(-1.75,-217.43,245.51,1.75,-215.83,246.91),ycyl(-1.75,246.21,0.7,-217.43,-215.83),ycyl(1.75,246.21,0.7,-217.43,-215.83)]))
# ---------- lower axis (y -220.20, z 239.19): shaft, left collar + washer, right dial
Y0,Z0=-220.20,239.19
G["P236"]=chk("P236",fuse([xcyl(Y0,Z0,1.8,3.88,17.51),xcone(Y0,Z0,1.8,1.6,17.51,17.71)]))
G["s237"]=chk("s237",xcyl(Y0,Z0,2.75,-12.30,-5.81))
G["s238"]=chk("s238",rd("work/g_solid_238.brep"))
G["s231"]=chk("s231",rd("work/g_solid_231.brep"))
d=fuse([xcyl(Y0,Z0,9.537,11.9,13.4),xcyl(Y0,Z0,3.537,13.3,16.9),xcone(Y0,Z0,3.537,2.287,16.9,17.4)])
fl=BRepFilletAPI_MakeFillet(d); ex=TopExp_Explorer(d,TopAbs_EDGE)
while ex.More():
    e=TopoDS.Edge_s(ex.Current()); c=BRepAdaptor_Curve(e)
    if c.GetType()==GeomAbs_Circle and abs(c.Circle().Radius()-9.537)<1e-3 and abs(c.Value(0).X()-13.4)<1e-3: fl.Add(0.5,e)
    ex.Next()
fl.Build(); d=fl.Shape()
pk=[(-214.29,234.98),(-222.51,232.31),(-227.45,239.19),(-222.44,246.08),(-214.40,243.54)]
d=cut(d,[xcyl(y,z,1.3,12.05 if y!=-227.45 else 12.6,13.6) for y,z in pk]+[ycyl(15.5,Z0,1.05,-225,-215)])
G["P232"]=chk("P232 dial",d)
# ---------- upper axis (y -220.20, z 263.50): shaft, block, aperture, knob
Y1,Z1=-220.20,263.50
G["shaftL"]=chk("shaftL",xcyl(Y1,Z1,1.95,-16.99,-2.74))
G["s239"]=chk("s239",xcyl(Y1,Z1,1.9,2.76,8.66))
G["P241"]=chk("P241",box(-2.74,-221.72,262.37,2.76,-218.0,266.55))
cap=common(ycyl(0,263.51,6.75,-225.9,-221.8),box(-7,-226,264.71,7,-221.7,271))
cap=cut(cap,[ycyl(x,269.47,1.0,-227,-221) for x in (-3.43,3.44)])
ap_=fuse([ycyl(0,263.51,4.75,-225.2,-221.8),cap])
G["P235"]=chk("P235 aperture",ap_)
k=fuse([xcone(Y1,Z1,2.45,3.45,-16.94,-16.44),xcyl(Y1,Z1,3.45,-16.44,-13.5),xcone(Y1,Z1,7.1,7.5,-13.54,-13.14),xcyl(Y1,Z1,7.5,-13.14,-10.84),
         xcone(Y1,Z1,7.5,7.1,-10.84,-10.44),xcyl(Y1,Z1,3.5,-10.5,-10.14)])
k=cut(k,[ycyl(-15.24,263.76,1.05,-226,-214),xcyl(-211.12,264.04,2.0,-14,-10)])
G["P234"]=chk("P234 knob",k)
allp=fuse(list(G.values())); allp=unify(allp)
chk("ALL",allp); print("faces",count(allp,TopAbs_FACE))
BRepTools.Write_s(allp,"work/rs_solid.brep")
