from __future__ import print_function

for name in ("abcdef", "abcxyz"):
    print("%s: %s" % (name, open(name, "r").read().rstrip()))
