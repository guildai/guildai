"""Module docstrings are expressions and not breakable.
"""


def foo():
    # A function definition line is breakable - this comment is not.
    123  # Numbers aren't breakable
    print("hello")  # breakable


foo  # Name not breakable
foo()  # Function call - breakable

x = 1  # Assignment - breakable

# Comments don't appear in the module AST so are never breakable.

"a string"  # String not breakable

for x in range(2):
    123
    print("hello from loop")

while x < 2:
    print("hello from while")
    x += 1

x  # Not breakable

# Expressions that are all breakable
d = {"a": 123}
del d["a"]
x + 1
x * 1
1 and 2
1 < 2


def bar():
    for i in range(2):
        print("hello bar from for")
        if i == 0:
            123
            print("hello bar from nested if")
        else:
            print("hello bar from nested else")
            "not breakable"
            object()  # breakable


[x for x in [1, 2, 3]]

if __name__ == "__main__":
    [1, 2, foo()]
    bar()

# Nothing breakable past this point
"hello"
1.123
{"foo": "bar"}
[1, 2, 3]
(1, 2, "hello")
{1, 2, 3}
