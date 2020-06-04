import argparse

p = argparse.ArgumentParser()
p.add_argument("--f1", default=1, type=int)
p.add_argument("--f2", default=1.1, type=float)
p.add_argument("--f3", default="hello", type=str)
p.add_argument("--f4", default=False, type=bool)

args, other = p.parse_known_args()

print("%r <%s>" % (args.f1, type(args.f1).__name__))
print("%r <%s>" % (args.f2, type(args.f2).__name__))
print("%r <%s>" % (args.f3, type(args.f3).__name__))
print("%r <%s>" % (args.f4, type(args.f4).__name__))

for arg in other:
    print("%r <%s>" % (arg, type(arg).__name__))
