msg = open("test.in").read().strip()
with open("test.out", "w") as f:
    f.write("Hello! %s\n" % msg)
