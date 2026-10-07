import sys
src=open("assemble.py").read().replace("src,solid_path,out=sys.argv[1:4]","src,solid_path,out=sys.argv[1],sys.argv[2],'work/dbg2.step'")
src=src.replace("st.UpdateAssemblies()","st.UpdateAssemblies()\nprint('newref name now:',repr(name(newref)),'| newcomp name:',repr(name(newcomp)),'| newref is shape-simple:',st.IsSimpleShape_s(newref),'| IsTopLevel:',st.IsTopLevel(newref))\ncomps=TDF_LabelSequence(); st.GetComponents_s(asm,comps)\nprint('assembly components:',comps.Length())\nr=TDF_Label(); st.GetReferredShape_s(newcomp,r); print('newcomp refers to name:',repr(name(r)),'same label as newref:',r.IsEqual(newref))")
exec(src)
