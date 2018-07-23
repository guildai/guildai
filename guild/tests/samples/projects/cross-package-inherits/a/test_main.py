from __future__ import print_function

import argparse

def main():
    p = argparse.ArgumentParser()
    p.add_argument("msg")
    p.add_argument("msg_file")
    args = p.parse_args()
    print(args.msg)
    print(open(args.msg_file, "r").read())

if __name__ == "__main__":
    main()
