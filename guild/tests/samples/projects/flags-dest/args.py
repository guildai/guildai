import argparse

p = argparse.ArgumentParser()
p.add_argument("--i", default=1, type=int)
p.add_argument("--f", default=1.234, type=float)
p.add_argument("--s", default="hello")
p.add_argument("--b", action="store_true")

args = p.parse_args()

print("i: %i" % args.i)
print("f: %f" % args.f)
print("s: %s" % args.s)
print("b: %s" % args.b)
