# Plugin Python utils

The module `guild.python_util` provides tools when working with Python
scripts and modules.

    >>> from guild import python_util

## Enumerating Python scripts

Some plugins can enumerate models in a location. To assist with this,
python utils provides `scripts_for_location`.

    >>> scripts = python_util.scripts_for_dir(
    ...   sample("scripts"), exclude=["*/__init__.py"])

Let's sort by name:

    >>> scripts.sort(key=lambda x: x.name)

The scripts:

    >>> [script.name for script in scripts]
    ['breakable_lines',
     'error',
     'flag_imports',
     'hello',
     'mnist_mlp',
     'no_breakable_lines',
     'sample_run']

## Script properties

Scripts can be inspected for various declarations. Let's example the
'mnist_mlp' script:

    >>> mnist_mlp = scripts[4]
    >>> mnist_mlp.name
    'mnist_mlp'

The script source can be read using the `src` attribute:

    >>> mnist_mlp.src
    '.../samples/scripts/mnist_mlp.py'

A script name is the base name (without extension) of the script
source:

    >>> mnist_mlp.name
    'mnist_mlp'

We can enumerate various script declarations.

Imports:

    >>> mnist_mlp.imports
    ['__future__',
     'print_function',
     'keras',
     'keras.datasets',
     'mnist',
     'keras.models',
     'Sequential',
     'keras.layers',
     'Dense',
     'Dropout',
     'keras.optimizers',
     'RMSprop']

Calls:

    >>> pprint([call.name for call in mnist_mlp.calls])
    ['load_data',
     'reshape',
     'reshape',
     'astype',
     'astype',
     'print',
     'print',
     'to_categorical',
     'to_categorical',
     'Sequential',
     'add',
     'add',
     'add',
     'add',
     'add',
     'summary',
     'compile',
     'fit',
     'evaluate',
     'print',
     'print',
     'Dense',
     'Dropout',
     'Dense',
     'Dropout',
     'Dense',
     'RMSprop',
     'TensorBoard']

 Params:

    >>> pprint(mnist_mlp.params)
    {'batch_size': 128, 'epochs': 20, 'num_classes': 10}

    >>> flag_imports = scripts[2]
    >>> flag_imports.name
    'flag_imports'

    >>> pprint(flag_imports.params)
    {'b': True, 'f': 1.0, 'i': 1, 'ii': 2, 's': 'hello'}

## Errors on init

A couple errors are generated when creating a script.

Syntax error:

    >>> script_path = path(mkdtemp(), "test.py")
    >>> write(script_path, "+++")
    >>> python_util.Script(script_path)
    Traceback (most recent call last):
    ...
      File "<unknown>", line 1
        +++
          ^
    SyntaxError: invalid syntax

The other error is when the file can't be read:

    >>> try:
    ...     python_util.Script("missing")
    ... except Exception as e:
    ...     print(e)
    ... else:
    ...     assert False
    [Errno 2] No such file or directory: 'missing'

## Sorting script objects

Script objects returned by `python_util` can be sorted according to
their path.

Create some scripts to sort.

    >>> to_sort = []
    >>> tmp = mkdtemp()
    >>> for name in ["c", "d", "a", "b"]:
    ...     script_path = path(tmp, name)
    ...     touch(script_path)
    ...     to_sort.append(python_util.Script(script_path))

    >>> [basename(script.src) for script in sorted(to_sort)]
    ['a', 'b', 'c', 'd']

## Wrapping methods

Plugins routinely patch the environment to perform additional
actions. One such patch is to listen for method calls on various
classes. The `listen_method` function can be used to reveive
notification when a method is called.

Let's create a class with a method that prints a message:

    >>> class Hello(object):
    ...   def say(self, msg):
    ...     print(msg)

Let's patch `say`:

    >>> def wrap_say(say, msg):
    ...   say("I've wrapped '%s'" % msg)
    >>> python_util.listen_method(Hello, "say", wrap_say)

When we call `hello` on an object:

    >>> hello = Hello()
    >>> hello.say("Hello Guild!")
    I've wrapped 'Hello Guild!'
    Hello Guild!

The arg `say` is the original wrapped function, which can be called by
the wrapping function.

We can wrap a method multiple times. In this case we'll wrap using an
instance method:

    >>> class Wrapper(object):
    ...   def __init__(self, cls, method_name):
    ...     python_util.listen_method(cls, method_name, self.wrap_say)
    ...
    ...   def wrap_say(self, say, msg):
    ...     say("I've also wrapped '%s'" % msg)

    >>> wrapper = Wrapper(Hello, "say")
    >>> hello.say("Hello again!")
    I've wrapped 'Hello again!'
    I've also wrapped 'Hello again!'
    Hello again!

A wrapper can circumvent the call to the original method and return
its own value by raising `python_util.Result`:

    >>> def wrap_and_prevent(say, msg):
    ...   say("I've wrapped '%s' and prevented the original call!" % msg)
    ...   raise python_util.Result(None)
    >>> python_util.listen_method(Hello, "say", wrap_and_prevent)
    >>> hello.say("Hello once more!")
    I've wrapped 'Hello once more!'
    I've also wrapped 'Hello once more!'
    I've wrapped 'Hello once more!' and prevented the original call!

Any errors generated by a wrapper as passed through. Let's illustrate
by creating a wrapper that generates an error:

    >>> def wrap_error(say, msg):
    ...    1 / 0

Let's add this function and call `say`:

    >>> python_util.listen_method(Hello, "say", wrap_error)
    >>> hello.say("And again!")
    Traceback (most recent call last):
    ZeroDivisionError: ...

We can remove wrappers using `remove_method_listener`:

    >>> python_util.remove_method_listener(hello.say, wrap_and_prevent)
    >>> python_util.remove_method_listener(hello.say, wrap_error)

    >>> hello.say("Again, once more!")
    I've wrapped 'Again, once more!'
    I've also wrapped 'Again, once more!'
    Again, once more!

Finally, we can remove all listeners on a method:

    >>> python_util.remove_method_listeners(hello.say)
    >>> hello.say("Hello, without listeners!")
    Hello, without listeners!

A method wrapper can access `self` associated with a method using
`python_util.wrapped_self`.

Here's a class that uses an instance attribute to define a message.

    >>> class Hello2(object):
    ...     msg = "Hello 2!"
    ...
    ...     def say(self):
    ...         print(self.msg)

    >>> Hello2().say()
    Hello 2!

And a wrapper that modifies the bound `self` for a wrapped function:

    >>> def wrap_say2(say):
    ...     self = python_util.wrapped_self(say)
    ...     self.msg = "Hello Two!"
    >>> python_util.listen_method(Hello2, "say", wrap_say2)

    >>> Hello2().say()
    Hello Two!

In our final example, we'll replace a method that increments a value
with a new function.

Here's our class and method:

    >>> class Calc(object):
    ...   def incr(self, x):
    ...     return x + 1

And our class and method in action:

    >>> calc = Calc()
    >>> calc.incr(1)
    2

Here's a function that supports a second argument, which specifies the
amount to increment by. Note we return a result by raising
`python_util.Result` (as in the previous example). Note we don't use
the original method (represented by the `_incr` argument) because
we're replacing it altogether.

    >>> def incr2(_incr, x, incr_by=1):
    ...   raise python_util.Result(x + incr_by)

We wrap the original:

    >>> python_util.listen_method(Calc, "incr", incr2)

And here's our new behavior:

    >>> calc.incr(1)
    2
    >>> calc.incr(1, 2)
    3

Let's unwrap and confirm that we no longer have access to the new
function:

    >>> python_util.remove_method_listener(Calc.incr, incr2)
    >>> calc.incr(1)
    2
    >>> calc.incr(1, 2)
    Traceback (most recent call last):
    TypeError: incr() takes ...

What happens when we add two listeners that both provide results? The
behavior is as follows:

- All listeners are notified, regardless of whether any have raised
  Result exceptions

- The last raised Result is returned as the result of the method call

Here are two listeners, both of which provide results:

    >>> def incr_by_2(_incr, x):
    ...    print("incr_by_2 called")
    ...    raise python_util.Result(x + 2)

    >>> def incr_by_3(_incr, x):
    ...    print("incr_by_3 called")
    ...    raise python_util.Result(x + 3)

Let's add both as listeners:

    >>> python_util.listen_method(Calc, "incr", incr_by_2)
    >>> python_util.listen_method(Calc, "incr", incr_by_3)

And test our method:

    >>> calc.incr(1)
    incr_by_2 called
    incr_by_3 called
    4

Here we see that both listeners were called, but result is returned
from the last to provide a result.

Let re-order our listeners to confirm:

    >>> python_util.remove_method_listeners(Calc.incr)
    >>> python_util.listen_method(Calc, "incr", incr_by_3)
    >>> python_util.listen_method(Calc, "incr", incr_by_2)

    >>> calc.incr(1)
    incr_by_3 called
    incr_by_2 called
    3

## Wrapping functions

Python util supports wrapping module functions as well as class
method.

Let's dynamically create a module for our tests:

    >>> import imp
    >>> howdy = imp.new_module("howdy")
    >>> howdy_def = """
    ... def say(msg):
    ...   print(msg)
    ... """
    >>> exec(howdy_def, howdy.__dict__)
    >>> import sys
    >>> sys.modules["howdy"] = howdy

Here's our function in action:

    >>> from howdy import say
    >>> say("Howdy!")
    Howdy!

We can wrap using a listener:

    >>> def say_again(say0, msg):
    ...   print(msg)

    >>> python_util.listen_function(howdy, "say", say_again)

Our current function remains unmodified:

    >>> say("Hi!")
    Hi!

To get our wrapper version we need to reimport the function.

    >>> from howdy import say
    >>> say("Hi!")
    Hi!
    Hi!

We can use multiple listeners.

    >>> python_util.listen_function(howdy, "say", say_again)
    >>> from howdy import say
    >>> say("Yo!")
    Yo!
    Yo!
    Yo!

To remove a listener, we use `remove_function_listener`:

    >>> python_util.remove_function_listener(say, say_again)
    >>> from howdy import say
    >>> say("What up?")
    What up?
    What up?

And to remove all listeners as use `remove_function_listeners`:

    >>> python_util.remove_function_listeners(say)
    >>> from howdy import say
    >>> say("How goes?")
    How goes?

A listener can circumvent a call to the wrapped function by raising a
`Result`.

    >>> def say_instead(_say0, msg):
    ...    print("I'm saying '%s' now!" % msg)
    ...    raise python_util.Result(None)
    >>> python_util.listen_function(howdy, "say", say_instead)
    >>> from howdy import say
    >>> howdy.say("Yop")
    I'm saying 'Yop' now!

Additional listeners still get notified.

    >>> python_util.listen_function(howdy, "say", say_again)

In this final test we'll just call the function directoy from our
module without reimporting it.

    >>> howdy.say("Bye!")
    I'm saying 'Bye!' now!
    Bye!

## Python module names

    >>> python_util.safe_module_name("hello")
    'hello'

    >>> python_util.safe_module_name("hello-there")
    'hello_there'

    >>> python_util.safe_module_name("train.py")
    'train'

## Executing scripts

`exec_script` is used to execute Python scripts. Scripts are specified
as file names with an optional global dict and module
name. `exec_script` returns the script globals dict used when
executing the script, which contains `__package__`, `__name__`, and
`__file__` items.

Here's a helper to execute a sample script:

    >>> def exec_sample(name, *args, **kw):
    ...     script = sample("scripts", name)
    ...     globals = python_util.exec_script(script, *args, **kw)
    ...     assert globals["__file__"] == script, (globals, script)
    ...     print((globals["__package__"], globals["__name__"]))

    >>> from guild.python_util import exec_script

Simple hello script:

    >>> exec_sample("hello.py")
    hello
    ('', '__main__')

    >>> exec_sample("hello.py", {"msg": "hola"})
    hola
    ('', '__main__')

Script in a package:

    >>> exec_sample("pkg/hello.py")
    hi from pkg
    ('', '__main__')

If a module attempts to import a package-relative module, it fails
unless an explicit package is specified:

    >>> try:
    ...     exec_sample("pkg/hello2.py")
    ... except Exception as e:
    ...     "relative import" in str(e), e
    (True, ...)

We can specify a package using `mod_name` to provide a
package-qualified module name. However, this fails unless the package
is in the system path.

    >>> try:
    ...     exec_sample("pkg/hello2.py", mod_name="pkg.hello2")
    ... except Exception as e:
    ...     "No module named" in str(e), e
    (True, ...)

When we specified the package and also make the package available, we
can execute the script.

    >>> with SysPath(prepend=[sample("scripts")]):
    ...     exec_sample("pkg/hello2.py", mod_name="pkg.hello2")
    hi from pkg
    ('pkg', 'hello2')

## Test Package Version

    >>> from guild.python_util import test_package_version

    >>> test_package_version("1", "1")
    True

    >>> test_package_version("1", "2")
    False

    >>> test_package_version("1", "<2")
    True

    >>> test_package_version("1.1", "<=1.2")
    True

    >>> test_package_version("0.7.0", ">=0.7.0")
    True

    >>> test_package_version("0.7.1", ">=0.7.0")
    True

    >>> test_package_version("0.7", ">=0.7.0")
    True

    >>> test_package_version("0.6", ">=0.7.0")
    False

    >>> test_package_version("0.66", ">=0.7.0")
    True

    >>> test_package_version("0.7.1.dev1", ">=0.7.0")
    True

This is unexpected but it's the actual behavior when you check for
pre-releases:

    >>> test_package_version("0.7.1.dev1", "<0.7.1")
    False

## Breakable Module Lines

The function `next_breakable_line` returns the next nearest breakable
line in a Python module.

    >>> from guild.python_util import next_breakable_line

We use the sample script `breakable_lines.py`:

    >>> breakable = sample("scripts", "breakable_lines.py")

The output generated by this script is nonsense but we test it as a
behavioral baseline.

    >>> run("%s %s" % (sys.executable, breakable))
    hello
    hello from loop
    hello from loop
    hello from while
    hello
    hello bar from for
    hello bar from nested if
    hello bar from for
    hello bar from nested else
    <exit 0>

Helper function to print a file with its breakable lines:

    >>> def print_breakable(filename):
    ...     for i, line in enumerate(open(filename).readlines()):
    ...         want_line = i + 1
    ...         line = line.rstrip()
    ...         try:
    ...             next_line = next_breakable_line(filename, want_line)
    ...         except TypeError as e:
    ...             assert "no breakable lines at or after %i" % want_line in str(e), e
    ...             print("%0.2i !!  %s" % (want_line, line))
    ...         else:
    ...             if want_line == next_line:
    ...                 print("%0.2i >>  %s" % (want_line, line))
    ...             else:
    ...                 print("%0.2i %0.2i  %s" % (want_line, next_line, line))

The output below shows each line along with the next line as returned
by `next_breakable_line`. If the next breakable line is the requested
line, `>>` is used to indicate that a break would occur there. If the
requested line does not have a next breakable line, `!!` is shown.

    >>> print_breakable(breakable)
    01 05  """Module docstrings are expressions and not breakable.
    02 05  """
    03 05
    04 05
    05 >>  def foo():
    06 08      # A function definition line is breakable - this comment is not.
    07 08      123  # Numbers aren't breakable
    08 >>      print("hello")  # breakable
    09 12
    10 12
    11 12  foo  # Name not breakable
    12 >>  foo()  # Function call - breakable
    13 14
    14 >>  x = 1  # Assignment - breakable
    15 20
    16 20  # Comments don't appear in the module AST so are never breakable.
    17 20
    18 20  "a string"  # String not breakable
    19 20
    20 >>  for x in range(2):
    21 22      123
    22 >>      print("hello from loop")
    23 24
    24 >>  while x < 2:
    25 >>      print("hello from while")
    26 >>      x += 1
    27 31
    28 31  x  # Not breakable
    29 31
    30 31  # Expressions that are all breakable
    31 >>  d = {"a": 123}
    32 >>  del d["a"]
    33 >>  x + 1
    34 >>  x * 1
    35 >>  1 and 2
    36 >>  1 < 2
    37 39
    38 39
    39 >>  def bar():
    40 >>      for i in range(2):
    41 >>          print("hello bar from for")
    42 >>          if i == 0:
    43 44              123
    44 >>              print("hello bar from nested if")
    45 46          else:
    46 >>              print("hello bar from nested else")
    47 48              "not breakable"
    48 >>              object()  # breakable
    49 51
    50 51
    51 >>  [x for x in [1, 2, 3]]
    52 53
    53 >>  if __name__ == "__main__":
    54 >>      [1, 2, foo()]
    55 >>      bar()
    56 !!
    57 !!  # Nothing breakable past this point
    58 !!  "hello"
    59 !!  1.123
    60 !!  {"foo": "bar"}
    61 !!  [1, 2, 3]
    62 !!  (1, 2, "hello")
    63 !!  {1, 2, 3}

And a script with no breakable lines:

    >>> print_breakable(sample("scripts", "no_breakable_lines.py"))
    01 !!  """Mod docstring."""
    02 !!
    03 !!  # Comment
    04 !!
    05 !!  123
    06 !!
    07 !!  "Some string"

The function `first_breakable_line(src)` is an alias for
`next_breakable_line(src, 1)`.

    >>> python_util.first_breakable_line(breakable)
    5
