"""Used to debug with --break and --break-at Guild run options."""

import submod

# Add 1 and 2
x = 1
y = 2
z = submod.add(x, y)

print("{x} + {y} = {z}".format(**locals()))

# Add 2 and 3
x = 3
y = 4
z = submod.add(x, y)

print("{x} + {y} = {z}".format(**locals()))
