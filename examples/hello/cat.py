import os
import sys

file = None

if file is None and os.path.exists("msg.out"):
    file = "msg.out"

print("Reading message from %s" % file, file=sys.stderr)
msg = open(file).read()
print(msg)

if file != "msg.out":
    print("Saving message to msg.out")
    open("msg.out", "w").write(msg)
