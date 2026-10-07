import sys; sys.path.insert(0,'.')
exec(open("final.py").read().replace("M=rd(sys.argv[1])","M=load(sys.argv[1])"))
