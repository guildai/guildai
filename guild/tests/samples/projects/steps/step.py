import argparse

p = argparse.ArgumentParser()
p.add_argument("--msg")
p.add_argument("--touch")

args = p.parse_args()

if args.msg:
    print(args.msg)

if args.touch:
    open(args.touch, "a").close()
