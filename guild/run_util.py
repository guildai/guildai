import guild.opdir
import guild.util

def run_status(rundir):
    """Run status based on op process status."""
    pid = _op_pid(rundir)
    if pid is None:
        return "stopped"
    elif guild.util.pid_exists(pid):
        return "running"
    else:
        return "crashed"

def op_pid(rundir):
    lockfile = guild.run.guild_file(rundir, "LOCK")
    try:
        raw = open(lockfile, "r").read()
    except (IOError, ValueError):
        return None
    else:
        return int(raw)

def extended_run_status(rundir):
    """Uses exit_status to extend the status to include error or success."""
    base_status = run_status(rundir)
    if base_status == "running":
        return "running"
    elif base_status == "crashed":
        return "terminated"
    elif base_status == "stopped":
        exit_status = guild.rundir.read_meta(rundir, "exit_status")
        if exit_status == "0":
            return "completed"
        else:
            return "error"
