import os
import sys

dir = sys.argv[1] if len(sys.argv) > 1 else os.path.join("target", ".guild")
for path in sorted(os.listdir(dir)):
    print(path)
