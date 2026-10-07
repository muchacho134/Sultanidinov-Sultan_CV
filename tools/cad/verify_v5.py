import sys, numpy as np
src=open("verify_v3.py").read()
src=src.replace('if short(k) not in ("P213","P111")','if short(k) not in CHANGED').replace('elif short(name(ref)) in ("P213","P111")','elif short(name(ref)) in CHANGED')
src=src.replace('for key,br in (("P213","work/p213_solid.brep"),("P111","work/sight_collar_solid.brep")):','for key,br in JOBS:')
CHANGED=("P259","P246","P150"); JOBS=(("P259","work/p259_solid.brep"),("P246","work/p246_solid.brep"),("P150","work/trio_solid.brep"))
exec(src)
