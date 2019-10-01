# Guild AI Sytle Guide

Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) unless
otherwise noted.

## Classes

The Guild codebase attempts to minimize class use in Python. In many
cases, this is not practical and there are many uses of classes
throughout. Nonetheless, if something can be accomplished using
builtin Python types and functions

Extendable interfaces should be implemented using classes. Even when
duck-typing, a class should define the expected interface.

Avoid inheritance whenever possible.

Do not use multiple inheritance.

### Class implementation (experimental)

The codebase uses two distinct patterns for class implementation:

    - Instance and static methods
    - External functions

Example of instance and static method use:

``` python
class Foo(object):

    def __init__(self, args):
        self.a = self._init_a(args)

    def _init_a(self, args):
        return self._a_from_args(args)

    @staticmethod
    def _a_from_args(args):
        return args.a

```

Pros:

- All Foo related code is associated with the Foo class
  - Easy to locate functions
  - Easy to remote functions related to Foo

Cons:

- Required use of `self` to call functions - this exposes object state
  when it's not otherwise needed

- Temptation to use order-dependent calls with side-effects to object
  state (this is an unfortunately used pattern in codebase)

- Required use of awkward `staticmethod` decorators

Example of external functions:

``` python
class Foo(object):

    def __init__(self, args):
        self.a = _foo_init_a(args)

def _foo_init_a(args):
    return _a_from_args(args)

def _a_from_args(args):
    return args.a
```

Alternatively:

``` python
class Foo(object):

    def __init__(self, args):
        _Foo_init(self, args)

def _Foo_init(foo, args):
    foo.a = _a_from_args(args)

def _a_from_args(args):
    return args.a
```

Pros:

- Natural use of functions
- Classes remain purely state and user-interface concerns

Cons:

- Requires some discipline to use this pattern and follow conventions
  (see below)
- Not strictly un-Pythonic but this is not a typical Python
  programming convention

**Conventions - Pattern 1**

1. Class methods are strictly used to:
   - Update state
   - Pass through a non-mutating call to a normal function
2. Use `_class_function_name` convention for normal functions that are
   tighly coupled to a class

**Conventions - Pattern 2**

1. Class methods are strictly used:
   - Pass through to a normal function
2. Use `_Class_function_name` naming convention for class-related
   functions
3. Position the object argument to class functions as the first
   argument

**General conventions**

1. Avoid functions that both modify an object and return a value -
   i.e. functions should be either read or write and not both
