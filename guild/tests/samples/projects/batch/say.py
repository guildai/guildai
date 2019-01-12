from __future__ import print_function

import argparse

p = argparse.ArgumentParser()
p.add_argument("--msg", default="hello")
p.add_argument("--loud", action="store_true")

args = p.parse_args()

msg = args.msg
if args.loud:
    msg = msg.upper()

print(msg)
