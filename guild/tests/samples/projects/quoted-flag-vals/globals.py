import pprint

f1 = 1
f2 = 1.1
f3 = 'hello'
f4 = True

print("%s <%s>" % (pprint.pformat(f1), type(f1).__name__))
print("%s <%s>" % (pprint.pformat(f2), type(f2).__name__))
print("%s <%s>" % (pprint.pformat(f3), type(f3).__name__))
print("%s <%s>" % (pprint.pformat(f4), type(f4).__name__))
