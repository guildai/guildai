x = 1
y = 2

open("file.txt", "w").write("%s + %s = %s" % (x, y, x + y))
