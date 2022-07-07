import sys

from guild.util import check_guild_version


def _patch():
    from guild import op
    from guild import python_util

    python_util.listen_function(op, "run", _patched_op_run)


def _patched_op_run(f0, op, *args, **kw):
    print("You're running %s" % op.opref.to_opspec())
    sys.stdout.flush()


if check_guild_version(">=0.7.1.dev1"):
    _patch()
