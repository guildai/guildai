from __future__ import print_function

import sys

file = "hello.txt"

print("Reading message from %s" % file, file=sys.stderr)
print(open(file).read())
