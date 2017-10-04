import imp
import os
import sys

if len(sys.argv) < 2:
    sys.stderr.write("missing required arg\n")
    sys.exit(1)
name = sys.argv[1]
f, path, desc = imp.find_module(name)
sys.argv = [os.path.abspath(path)] + sys.argv[2:]
imp.load_module("__main__", f, path, desc)
