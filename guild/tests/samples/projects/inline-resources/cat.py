import os
import sys

for path in sys.argv[1:]:
    if not os.path.exists(path):
        sys.stderr.write("cat: no such file %r" % path)
        sys.exit(1)
    print(open(path).read())
