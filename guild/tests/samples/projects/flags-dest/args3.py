import argparse

p = argparse.ArgumentParser()
p.add_argument("--x", nargs="+")
p.add_argument("--y", nargs="+", type=int)

args = p.parse_args()
print(args.x)
print(args.y)
