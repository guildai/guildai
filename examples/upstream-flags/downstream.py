import yaml

from guild import op_util

x = 3
y = 4

upstream_flags = yaml.load(open("upstream-flags.yml"))
run = op_util.current_run()
flags = run["flags"]
flags.update({"upstream-%s" % name: val for name, val in upstream_flags.items()})
run.write_attr("flags", flags)

print("upstream:   %s" % open("upstream-file.txt").read())
print("downstream: %s + %s = %s" % (x, y, x + y))
