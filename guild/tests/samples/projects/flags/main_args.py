import argparse

p = argparse.ArgumentParser()
p.add_argument("--foo", type=int, default=1, choices=(1, 2), help="Foo")
p.add_argument("--bar", type=float, default=0.001, help="Bar")

args = p.parse_args()
print("bar: {}".format(args.bar))
print("foo: {}".format(args.foo))
