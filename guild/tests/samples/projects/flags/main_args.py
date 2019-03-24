import argparse

p = argparse.ArgumentParser()
p.add_argument("--foo", default=1, choices=(1, 2), help="Foo")
p.add_argument("--bar", default=0.001, help="Bar")

args = p.parse_args()
print("foo: {}".format(args.foo))
print("bar: {}".format(args.bar))
