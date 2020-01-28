import argparse

p = argparse.ArgumentParser()
p.add_argument("--bar", default=456)

if __name__ == "__main__":
    args = p.parse_args()
    print("bar: %s", args.bar)
