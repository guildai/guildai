from __future__ import absolute_import


def fail():
    c1()


def c1():
    c2()


def c2():
    import exception


fail()
