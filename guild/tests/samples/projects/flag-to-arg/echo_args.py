import argparse

p = argparse.ArgumentParser()
p.add_argument("--x")

args = p.parse_args()

print(repr(args.x))
