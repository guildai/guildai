from __future__ import absolute_import
from __future__ import print_function

assert __name__ == "__main__", __name__
assert __package__ == "pkg", __package__

from . import main_impl


def run():
    print("hello from %s in %s" % (__name__, __package__))
    main_impl.run()


if __name__ == "__main__":
    run()
