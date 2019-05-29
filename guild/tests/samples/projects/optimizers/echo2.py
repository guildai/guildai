i = 3
f = 2.0
b = True
s = "hello"

assert isinstance(i, int), i
assert isinstance(f, float), f
assert isinstance(b, bool), b

print("i: %i" % i)
print("f: %f" % f)
print("f: %s" % b)
print("s: %s" % s)

print("loss: %f" % (f - 1))
