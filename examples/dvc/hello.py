msg = "Hello %s!" % open("hello.in").read().strip()
print(msg)
with open("hello.out", "w") as f:
    f.write("%s\n" % msg)
