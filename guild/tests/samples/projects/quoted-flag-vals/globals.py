import pprint

f1 = None
f2 = None
f3 = None
f4 = None

if f1 is not None:
    print("%s <%s>" % (pprint.pformat(f1), type(f1).__name__))

if f2 is not None:
    print("%s <%s>" % (pprint.pformat(f2), type(f2).__name__))

if f3 is not None:
    print("%s <%s>" % (pprint.pformat(f3), type(f3).__name__))

if f4 is not None:
    print("%s <%s>" % (pprint.pformat(f4), type(f4).__name__))
