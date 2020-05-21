from __future__ import print_function

import sys

to_print = sys.argv[1:]
for name, val in zip(to_print[0::2], to_print[1::2]):
    print(name, repr(val))
