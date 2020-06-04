from __future__ import print_function

import os

i = 1
f = 1.1
s = "hello"
b1 = True
b2 = False

print("globals:", i, f, s, b1, b2)

for name in sorted(os.environ):
    if name.startswith("FLAG_"):
        print("env %s:" % name, os.environ[name])
