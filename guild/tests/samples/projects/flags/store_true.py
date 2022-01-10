import argparse

p = argparse.ArgumentParser()
p.add_argument("--foo", action="store_true")
args = p.parse_args()
print(args.foo)
