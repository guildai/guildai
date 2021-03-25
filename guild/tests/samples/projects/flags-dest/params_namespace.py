try:
    from type import SimpleNamespace
except ImportError:

    class SimpleNamespace(object):
        def __init__(self, **kw):
            self.__dict__.update(kw)

        def __str__(self):
            from pprint import pformat

            return "namespace(%s)" % ", ".join(
                ["%s=%s" % (name, val) for name, val in sorted(self.__dict__.items())]
            )


params = SimpleNamespace(
    i=123,
    f=1.123,
    s="hello",
    b=False,
    l=[1, 2, "foo"],
)

print(params)
