import argparse

p = argparse.ArgumentParser()
p.add_argument("--base-foo", default=1, type=int)

subp = p.add_subparsers()
p_a = subp.add_parser("a")
p_a.add_argument("--a-foo", default=2, type=int)

p_b = subp.add_parser("b")
p_b.add_argument("--b-foo", default=3, type=int)

print(p.parse_args())
