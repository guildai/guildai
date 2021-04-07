import argparse

p = argparse.ArgumentParser()
p.add_argument("--base-foo", default=1, type=int)

subp = p.add_subparsers()
p_a = subp.add_parser("a")
p_a.add_argument("--a-foo", default=2, type=int)

p_b = subp.add_parser("b")
p_b.add_argument("--b-foo", default=3, type=int)

args = p.parse_args()

print("base_foo=%i" % args.base_foo)
if hasattr(args, "a_foo"):
    print("a_foo=%i" % args.a_foo)
if hasattr(args, "b_foo"):
    print("b_foo=%i" % args.b_foo)
