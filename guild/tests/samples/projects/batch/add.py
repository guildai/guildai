import argparse

p = argparse.ArgumentParser()
p.add_argument("--x", type=int, required=True)
p.add_argument("--y", type=int, required=True)
p.add_argument("--z", type=int, required=True)

args = p.parse_args()

print(sum([args.x, args.y, args.z]))
