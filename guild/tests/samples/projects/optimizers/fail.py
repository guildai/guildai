import sys

code = 1


def fail():
    # Indication used to generate a stack for debug info (line
    # numbers, etc.)
    fail2()


def fail2():
    if code == 1:
        raise Exception("FAIL")
    if code != 0:
        sys.stderr.write("FAIL\n")
    sys.exit(code)


fail()
