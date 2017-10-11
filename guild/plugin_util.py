"""Util functions used by plugins at op runtime.
"""

import sys

import guild.run

class NoCurrentRun(Exception):
    pass

def exit(msg, exit_status=1):
    """Exit the Python runtime with a message.
    """
    sys.stderr.write(msg)
    sys.stderr.write("\n")
    sys.exit(exit_status)

def current_run():
    """Returns an instance of guild.run.Run for the current run.

    The current run directory must be specified with the RUNDIR
    environment variable. If this variable is not defined, raised
    NoCurrentRun.
    """
    path = os.getenv("RUNDIR")
    if not path:
        raise NoCurrentRun()
    run_id = os.path.basename(path)
    return guild.run.Run(run_id, path)
