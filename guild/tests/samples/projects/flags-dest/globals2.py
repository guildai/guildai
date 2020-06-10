# Example of modifying a flag after an initial assignment. Guild
# should support setting the initial value but not change any of the
# subsequent modification behavior.

from __future__ import print_function

i = 1
j = i + 1  # not treated as a flag

if i == 2:
    i = 3
    j = 4
elif i == 3:
    for i in range(10):
        i = 33
        j = 44

print(i, j)
