from __future__ import print_function

import argparse

p = argparse.ArgumentParser()
p.add_argument("--i", type=int, default=1)
p.add_argument("--f", type=float, default=1.1)
p.add_argument("--s", default="hello")
p.add_argument("--b", action="store_true")

args = p.parse_args()

prefix = "Flags:"

print(prefix, args.i, args.f, args.b, args.s)
