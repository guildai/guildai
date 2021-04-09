import glob

for path in glob.glob("x-*"):
    print("found %s" % path)
