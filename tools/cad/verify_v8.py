import sys, numpy as np
src=open("verify_v3b.py").read()
src=src.replace('if short(k) not in ("P213","P111")','if short(k) not in CHANGED').replace('elif short(name(ref)) in ("P213","P111")','elif short(name(ref)) in CHANGED')
src=src.replace('for key,br in (("P213","work/p213_solid.brep"),("P111","work/sight_collar_solid.brep")):','for key,br in JOBS:')
CHANGED=("P596",); JOBS=(("P596","work/hous_solid.brep"),)
exec(src)
