from __future__ import print_function

import sys

file = "hello.txt"

sys.stderr.write("Reading message from %s\n" % file)
print(open(file).read())
