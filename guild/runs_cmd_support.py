import click

import guild.click_util

RUN_ARG_HELP = """
RUN may be a run ID (or the unique start of a run ID) or a zero-based
index corresponding to a run returned by the list command. Indexes may
also be specified in ranges in the form START:END where START is the
start index and END is the end index. Either START or END may be
omitted. If START is omitted, all runs up to END are selected. If END
id omitted, all runs from START on are selected. If both START and END
are omitted (i.e. the ':' char is used by itself) all runs are selected.
"""

def run_scope_options(fn):
    guild.click_util.append_params(fn, [
        click.Option(
            ("-p", "--project", "project_location"),
            help=("Project location (file system directory) for filtering "
                  "runs."),
            metavar="LOCATION"),
        click.Option(
            ("-S", "--system"),
            help=("Include system wide runs rather than limit to runs "
                  "associated with a project location. Ignores LOCATION."),
            is_flag=True)
    ])
    return fn

def run_filters(fn):
    guild.click_util.append_params(fn, [
        click.Option(
            ("-m", "--model", "models"),
            metavar="MODEL",
            help="Include only runs for MODEL.",
            multiple=True),
        click.Option(
            ("-r", "--running", "status"),
            help="Include only runs that are still running.",
            flag_value="running"),
        click.Option(
            ("-c", "--completed", "status"),
            help="Include only completed runs.",
            flag_value="completed"),
        click.Option(
            ("-s", "--stopped", "status"),
            help=("Include only runs that exited with an error or were "
                  "terminated by the user."),
            flag_value="stopped"),
        click.Option(
            ("-e", "--error", "status"),
            help="Include only runs that exited with an error.",
            flag_value="error"),
        click.Option(
            ("-t", "--terminated", "status"),
            help="Include only runs terminated by the user.",
            flag_value="terminated"),
    ])
    return fn

def runs_list_options(fn):
    run_scope_options(fn)
    run_filters(fn)
    guild.click_util.append_params(fn, [
        click.Option(
            ("-v", "--verbose"),
            help="Show run details.",
            is_flag=True),
        click.Option(
            ("-d", "--deleted"),
            help="Show deleted runs.",
            is_flag=True),
    ])
    return fn
