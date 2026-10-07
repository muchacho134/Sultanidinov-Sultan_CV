import sys
mode=sys.argv[3]
src=open("assemble.py").read().replace("src,solid_path,out=sys.argv[1:4]","src,solid_path,out=sys.argv[1],sys.argv[2],'work/var_%s.step'"%mode)
if mode=="A":   # replace shape only, keep 266 untouched
    src=src.replace("st.RemoveComponent(comp266)","pass").replace("try: st.RemoveShape(ref266,True)","try: pass")
if mode=="B":   # remove component only, don't remove label
    src=src.replace("try: st.RemoveShape(ref266,True)","try: pass")
exec(src)
