import argparse
import sys

p = argparse.ArgumentParser()
p.add_argument("--rundir")
p.add_argument("--message")
p.add_argument("--file")
p.add_argument("--file-output", action="store_true")

args = p.parse_args()

def say(msg):
    print(msg)
    open("output", "w").write(msg)

if args.file_output:
    say("Latest from-file output:")
    say(open("from-file/output", "r").read())
elif args.file:
    try:
        out = open(args.file, "r").read()
    except IOError as e:
        sys.stderr.write("Error reading %s: %s\n" % (args.file, e))
        sys.exit(1)
    else:
        say(out)
elif args.message:
    say(args.message)
else:
    say("Hello Guild!")
