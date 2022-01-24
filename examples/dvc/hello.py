msg = open("hello.in").read().strip()
with open("hello.out", "w") as f:
    f.write("Hello! %s\n" % msg)
