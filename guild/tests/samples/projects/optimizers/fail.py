import sys

code = 1


def fail():
    fail2()


def fail2():
    if code != 1:
        sys.stderr.write("FAIL\n")
        sys.exit(code)
    raise Exception("FAIL")


fail()
