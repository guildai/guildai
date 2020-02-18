import argparse

p = argparse.ArgumentParser()
p.add_argument("--foo", default=object())

p.parse_args()
