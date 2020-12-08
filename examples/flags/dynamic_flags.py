"""Example of dynamically updating the current run flags.

This practice is a solid anti-pattern. Flags should be defined up
front and not generated dynamically. However, it may be convenient in
some cases to dynamically generate flags at runtime so they appear
alongside other run flags. One use-case that comes to mind is to
provide generated parameters used by an operation that are not
user-provided. E.g. network architecture, layer count, etc.
"""

from guild import op_util

x = 1
y = 2

z = x + y
print("Dynamically adding flag z=%s" % z)
run = op_util.current_run()
flags = run["flags"]
flags["z"] = z
run.write_attr("flags", flags)
