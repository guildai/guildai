import argparse

p1 = argparse.ArgumentParser(add_help=False)
p1.add_argument("--a", default="A")
p1.add_argument("--b", default="B")

p2 = argparse.ArgumentParser(parents=[p1])
p2.add_argument("--c", default="C")

print(p2.parse_args())
