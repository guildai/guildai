import sys

for i, arg in enumerate(sys.argv[1:]):
    if i > 0:
        sys.stdout.write(" ")
    sys.stdout.write(arg)
sys.stdout.write("\n")
