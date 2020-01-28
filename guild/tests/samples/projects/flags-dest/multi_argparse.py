import argparse

import submod  # Side effect of building a second parser.

p = argparse.ArgumentParser()
p.add_argument("--foo", default=123)

if __name__ == "__main__":
    args = p.parse_args()
    print("foo: %s" % args.foo)
