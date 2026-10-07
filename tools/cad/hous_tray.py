exec(open("hous_build.py").read().split("# ---- box profile")[0])
A=lambda cz,cy:('A',(cz,cy))
from OCP.BRepBuilderAPI import BRepBuilderAPI_MakeFace
def sheet(poly,d=1.5):
    """thicken open polyline profile by d toward the closing chord side"""
    w=wire(poly); m=BRepOffsetAPI_MakeOffset(w,GeomAbs_Arc,True); m.Perform(d); sw=m.Shape()
    ex=TopExp_Explorer(sw,TopAbs_WIRE); sf=BRepBuilderAPI_MakeFace(TopoDS.Wire_s(ex.Current()),True).Face()
    C=face(poly+[poly[0]]); return sf,C
def sheet_prism(poly,x0,x1,d=1.5):
    C=face(poly+[poly[0]]); Ci=off2d(C,-d)
    a=poly[0]; b=poly[-1]; import math
    t=((b[0]-a[0]),(b[1]-a[1])); L=math.hypot(*t); t=(t[0]/L,t[1]/L); n=(-t[1],t[0])
    mid=((a[0]+b[0])/2+n[0],(a[1]+b[1])/2+n[1])
    # pick the normal pointing into C
    from OCP.BRepClass import BRepClass_FaceClassifier
    from OCP.TopAbs import TopAbs_IN
    if BRepClass_FaceClassifier(C,P(0,mid),1e-6).State()!=TopAbs_IN: n=(-n[0],-n[1])
    e=4*d; a0=(a[0]-t[0]*e,a[1]-t[1]*e); b0=(b[0]+t[0]*e,b[1]+t[1]*e)
    w_=1.05*d; Q=face([a0,b0,(b0[0]+n[0]*w_,b0[1]+n[1]*w_),(a0[0]+n[0]*w_,a0[1]+n[1]*w_),a0])
    return cut(prism(C,x0,x1),[prism(Ci,x0-1,x1+1),prism(Q,x0-1,x1+1)])
TAILBOX=[(217.38,-346.90),A(217.38,-331.20),(230.02,-340.52),A(232.43,-342.30),(232.43,-339.30),(259.81,-339.30),A(259.81,-336.30),(262.81,-336.30),
         (262.81,-332.09),A(265.81,-332.09),(264.38,-329.45),(285.97,-317.80),(285.97,-309.14)]
TAILCH=[(217.38,-346.90),A(217.38,-331.20),(230.02,-340.52),A(232.43,-342.30),(232.43,-339.30),(250.33,-339.30),(262.81,-332.57),
         (262.81,-332.09),A(265.81,-332.09),(264.38,-329.45),(285.97,-317.80),(285.97,-309.14)]
TA=[(188.93,-317.70),(188.93,-345.77),A(194.78,-331.20),(194.78,-346.90)]+TAILBOX
TB=[(177.91,-334.70),A(175.29,-339.54),(180.35,-337.38),A(194.78,-331.20),(194.78,-346.90)]+TAILCH
SL=[(262.81,-336.30),(262.81,-332.09),A(265.81,-332.09),(264.38,-329.45),(285.97,-317.80),(285.97,-309.14)]
parts=[]
parts.append(chk("TA",sheet_prism(TA,-15.7,-10.7)))
parts.append(chk("TB",sheet_prism(TB,-10.7,12.7)))
parts.append(chk("slope",common(sheet_prism(TA,-32.5,-15.7),box(-33,-350,262.81,-15.7,-300,290))))
# side plate x 12.7..15.7
PLATE=[(172.38,-331.50),A(175.38,-331.50),(175.38,-334.50),(177.50,-334.50),A(175.29,-339.54),(180.35,-337.38),A(194.78,-331.20),(194.78,-346.90)]+TAILCH+\
      [(261.02,-317.54),(260.07,-317.70),(175.18,-317.70),A(175.18,-320.50),(172.38,-320.50),(172.38,-331.50)]
fP=face(PLATE); plate=prism(fP,12.7,15.7)
def xcyl(z,y,r,x0,x1): return BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(x0,y,z),gp_Dir(1,0,0)),r,x1-x0).Shape()
def slot(y,z0,z1,x0,x1,r=1.5): return fuse([box(x0,y-r,z0,x1,y+r,z1),xcyl(z0,y,r,x0,x1),xcyl(z1,y,r,x0,x1)])
holes=[slot(y,193.68,217.68,12.0,16.5) for y in (-341.2,-336.2,-326.2,-321.2)]+[slot(-331.2,183.68,227.68,12.0,16.5)]
holes+=[xcyl(185.88,-335.71,1.55,12.0,16.5),xcyl(274.66,-318.26,1.55,12.0,16.5),xcyl(185.88,-335.71,3.0,14.7,16.5),xcyl(274.66,-318.26,3.0,14.7,16.5)]
parts.append(chk("plate",plate))
# front gusset x -10.7..-9.2 (plate outline, z<212.45)
gus=common(prism(fP,-10.7,-9.2),box(-11,-350,170,-9,-310,212.45)); parts.append(chk("gusset",gus))
# mounting ear x -14.5..-11.7
EAR=[(264.38,-329.45),(285.97,-317.80),(285.97,-305.28),(278.94,-305.28),A(255.60,-307.11),(268.30,-287.44),A(246.31,-301.30),(261.31,-322.54),(264.38,-329.45)]
ear=prism(face(EAR),-14.5,-11.7); parts.append(chk("ear",ear)); holes.append(xcyl(282.97,-313.78,1.6,-15,-11))
HOOK=[(180.35,-337.38),A(175.29,-339.54),(175.29,-334.04),(172.07,-334.04),A(172.07,-330.34),(168.376,-330.34),A(172.07,-330.34),(172.07,-326.646),(180.35,-326.646),(180.35,-337.38)]
parts.append(chk("hook",prism(face(HOOK),-5.5,5.5)))
import math
nd=(0.88,-0.47); L_=math.hypot(*nd); nd=(nd[0]/L_,nd[1]/L_)   # (y,z) axis pointing into the part
ax=gp_Ax2(gp_Pnt(0,-340.72,260.34),gp_Dir(0,nd[0],nd[1]))
parts.append(chk("boss",BRepPrimAPI_MakeCylinder(ax,6.0,7.8).Shape()))
holes.append(BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(0,-340.72-nd[0],260.34-nd[1]),gp_Dir(0,nd[0],nd[1])),2.55,12).Shape())
# P593 pin merged (R1.3 down from top skin), top R6 hole
box_=rd("work/hous_box.brep")
pin=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(-20.7,-289.92,222.13),gp_Dir(0,1,0)),1.3,289.92-275.9).Shape()
topH=BRepPrimAPI_MakeCylinder(gp_Ax2(gp_Pnt(-52.2,-280,226.71),gp_Dir(0,1,0)),6.0,10).Shape()
allp=fuse([box_]+parts+[pin]); res=cut(allp,holes+[topH]); res=unify(res)
chk("housing",res); print("faces",count(res,TopAbs_FACE))
BRepTools.Write_s(res,"work/hous_solid.brep")
