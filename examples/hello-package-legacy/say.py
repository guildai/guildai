import argparse
import sys
import time


def say(msg):
    print(msg)
    with open("output", "a") as f:
        f.write(msg)
        f.write("\n")


def say_output():
    say("Latest from-file output:")
    say(open("from-file/output", "r").read().rstrip())


def say_file(path):
    say(_read_file(path))


def _read_file(path):
    try:
        return open(path, "r").read()
    except IOError as e:
        sys.stderr.write("Error reading %s: %s\n" % (path, e))
        sys.exit(1)


def say_default():
    say("Hello Guild!")


def main():
    args = _parse_args()
    if args.loop:
        for _ in range(args.loop):
            _main(args)
            time.sleep(1)
    else:
        _main(args)


def _main(args):
    if args.file_output:
        say_output()
    elif args.file:
        say_file(args.file)
    elif args.message:
        say(args.message)
    else:
        say_default()


def _parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--rundir")
    p.add_argument("--message")
    p.add_argument("--file")
    p.add_argument("--file-output", action="store_true")
    p.add_argument("--loop", type=int)
    return p.parse_args()


if __name__ == "__main__":
    main()
