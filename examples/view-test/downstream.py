import os

if os.path.exists("required-file.txt"):
    print("Found require-file.txt")
    print(open("required-file.txt").read())
else:
    print("ERROR: required-file.txt missing")
    raise SystemExit(1)
