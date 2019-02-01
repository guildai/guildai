import sys

try:
    count = len(sys.argv) > 1 and int(sys.argv[1]) or 0
except TypeError:
    count = 0

for file_i in range(count):
    f = open("file-%i" % (file_i + 1), "w")
    for arg_i, arg in enumerate(sys.argv[2:]):
        if arg_i > 0:
            f.write(" ")
        f.write(arg)
    f.write("\n")
    f.close()
