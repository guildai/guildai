# Command help

Guild provides help text to users with the `--help` option.

    >>> run("guild --help")  # doctest: +REPORT_UDIFF
    Usage: guild [OPTIONS] COMMAND [ARGS]...
    <BLANKLINE>
      Guild AI command line interface.
    <BLANKLINE>
    Options:
      --version  Show the version and exit.
      -C PATH    Use PATH as current directory for a command.
      -H PATH    Use PATH as Guild home.
      --debug    Log more information during command.
      --help     Show this message and exit.
    <BLANKLINE>
    Commands:
      api              CLI based API calls.
      cat              Show contents of a run file.
      check            Check the Guild setup.
      comment          Add or remove run comments.
      compare          Compare run results.
      completion       Generate command completion script.
      diff             Diff two runs.
      download         Download a file resource.
      export           Export one or more runs.
      help             Show help for a path or package.
      import           Import one or more runs from ARCHIVE.
      init             Initialize a Guild environment.
      install          Install one or more packages.
      label            Set run labels.
      ls               List run files.
      mark             Mark a run.
      merge            Copy run files to a project directory.
      models           Show available models.
      open             Open a run path or output.
      operations, ops  Show model operations.
      package          Create a package for distribution.
      packages         Show or manage packages.
      publish          Publish one or more runs.
      pull             Copy one or more runs from a remote location.
      push             Copy one or more runs to a remote location.
      remote           Manage remote status.
      remotes          Show available remotes.
      run              Run an operation.
      runs             Show or manage runs.
      search           Search for a package.
      select           Select a run and shows its ID.
      shell            Start a Python shell for API use.
      stop             Stop one or more runs.
      sync             Synchronize remote runs.
      sys              System utilities.
      tag              Add or remove run tags.
      tensorboard      Visualize runs with TensorBoard.
      tensorflow       Collection of TensorFlow tools.
      uninstall        Uninstall one or more packages.
      view             Visualize runs in a local web application.
      watch            Watch run output.

    >>> run("guild runs --help")  # doctest: +REPORT_UDIFF
    Usage: guild runs [OPTIONS] COMMAND [ARGS]...
    <BLANKLINE>
      Show or manage runs.
    <BLANKLINE>
      If COMMAND is omitted, lists runs. Refer to 'guild runs list --help' for
      more information on the list command.
    <BLANKLINE>
    Options:
      -a, --all                       Show all runs (by default only the last 20
                                      runs are shown).
    <BLANKLINE>
      -m, --more                      Show 20 more runs. Maybe used multiple
                                      times.
    <BLANKLINE>
      -n, --limit N                   Limit number of runs shown.
      -d, --deleted                   Show deleted runs.
      -A, --archive PATH              Show archived runs in PATH.
      -c, --comments                  Show run comments.
      -v, --verbose                   Show run details.
      --json                          Format runs as JSON.
      -s, --simplified                Show a simplified list.
      -F, --filter EXPR               Filter runs using a filter expression. See
                                      Filter by Expression above for details.
    <BLANKLINE>
      -Fo, --operation VAL            Filter runs with operations matching VAL.
      -Fl, --label VAL                Filter runs with labels matching VAL. To
                                      show unlabeled runs, use --unlabeled.
    <BLANKLINE>
      -Fu, --unlabeled                Filter runs without labels.
      -Ft, --tag TAG                  Filter runs with TAG.
      -Fc, --comment VAL              Filter runs with comments matching VAL.
      -Fm, --marked                   Filter marked runs.
      -Fn, --unmarked                 Filter unmarked runs.
      -Fs, --started RANGE            Filter runs started within RANGE. See above
                                      for valid time ranges.
    <BLANKLINE>
      -Fd, --digest VAL               Filter runs with a matching source code
                                      digest.
    <BLANKLINE>
      -Sr, --running / --not-running  Filter runs that are still running.
      -Sc, --completed / --not-completed
                                      Filter completed runs.
      -Se, --error / --not-error      Filter runs that exited with an error.
      -St, --terminated / --not-terminated
                                      Filter runs terminated by the user.
      -Sp, --pending / --not-pending  Filter pending runs.
      -Ss, --staged / --not-staged    Filter staged runs.
      -r, --remote REMOTE             List runs on REMOTE rather than local runs.
      --help                          Show this message and exit.
    <BLANKLINE>
    Commands:
      comment     Add or remove run comments.
      delete, rm  Delete one or more runs.
      diff        Diff two runs.
      export      Export one or more runs.
      import      Import one or more runs from ARCHIVE.
      info        Show run information.
      label       Set run labels.
      list        List runs.
      mark        Mark a run.
      merge       Copy run files to a project directory.
      publish     Publish one or more runs.
      pull        Copy one or more runs from a remote location.
      purge       Permanentaly delete one or more deleted runs.
      push        Copy one or more runs to a remote location.
      restore     Restore one or more deleted runs.
      stop        Stop one or more runs.
      tag         Add or remove run tags.

Help content can be generated as JSON for a command by setting the
`GUILD_HELP_JSON` to `1`.

    >>> with Env({"GUILD_HELP_JSON": "1"}):
    ...     out = run_capture("guild runs --help")

NOTE: There is a problem comparing output on Windows that causes false
errors in the following assertion. When the output is pasted verbatim
the line below fails with an empty banner `Differences (unified diff
with -expected +actual):`

    >>> pprint(json.loads(out))  # doctest: +REPORT_UDIFF -NORMALIZE_PATHS
    {'commands': [{'help': 'Add or remove run comments.', 'term': 'comment'},
                  {'help': 'Delete one or more runs.', 'term': 'delete, rm'},
                  {'help': 'Diff two runs.', 'term': 'diff'},
                  {'help': 'Export one or more runs.', 'term': 'export'},
                  {'help': 'Import one or more runs from `ARCHIVE`.',
                   'term': 'import'},
                  {'help': 'Show run information.', 'term': 'info'},
                  {'help': 'Set run labels.', 'term': 'label'},
                  {'help': 'List runs.', 'term': 'list'},
                  {'help': 'Mark a run.', 'term': 'mark'},
                  {'help': 'Copy run files to a project directory.',
                   'term': 'merge'},
                  {'help': 'Publish one or more runs.', 'term': 'publish'},
                  {'help': 'Copy one or more runs from a remote location.',
                   'term': 'pull'},
                  {'help': 'Permanentaly delete one or more deleted runs.',
                   'term': 'purge'},
                  {'help': 'Copy one or more runs to a remote location.',
                   'term': 'push'},
                  {'help': 'Restore one or more deleted runs.', 'term': 'restore'},
                  {'help': 'Stop one or more runs.', 'term': 'stop'},
                  {'help': 'Add or remove run tags.', 'term': 'tag'}],
     'help': 'Show or manage runs.\n'
             '\n'
             'If `COMMAND` is omitted, lists runs. Refer to ``guild runs list\n'
             '--help`` for more information on the `list` command.',
     'options': [{'help': 'Show all runs (by default only the last 20 runs are '
                          'shown).',
                  'term': '-a, --all'},
                 {'help': 'Show 20 more runs. Maybe used multiple times.',
                  'term': '-m, --more'},
                 {'help': 'Limit number of runs shown.', 'term': '-n, --limit N'},
                 {'help': 'Show deleted runs.', 'term': '-d, --deleted'},
                 {'help': 'Show archived runs in PATH.',
                  'term': '-A, --archive PATH'},
                 {'help': 'Show run comments.', 'term': '-c, --comments'},
                 {'help': 'Show run details.', 'term': '-v, --verbose'},
                 {'help': 'Format runs as JSON.', 'term': '--json'},
                 {'help': 'Show a simplified list.', 'term': '-s, --simplified'},
                 {'help': 'Filter runs using a filter expression. See Filter by '
                          'Expression above for details.',
                  'term': '-F, --filter EXPR'},
                 {'help': 'Filter runs with operations matching `VAL`.',
                  'term': '-Fo, --operation VAL'},
                 {'help': 'Filter runs with labels matching VAL. To show unlabeled '
                          'runs, use --unlabeled.',
                  'term': '-Fl, --label VAL'},
                 {'help': 'Filter runs without labels.',
                  'term': '-Fu, --unlabeled'},
                 {'help': 'Filter runs with TAG.', 'term': '-Ft, --tag TAG'},
                 {'help': 'Filter runs with comments matching VAL.',
                  'term': '-Fc, --comment VAL'},
                 {'help': 'Filter marked runs.', 'term': '-Fm, --marked'},
                 {'help': 'Filter unmarked runs.', 'term': '-Fn, --unmarked'},
                 {'help': 'Filter runs started within RANGE. See above for valid '
                          'time ranges.',
                  'term': '-Fs, --started RANGE'},
                 {'help': 'Filter runs with a matching source code digest.',
                  'term': '-Fd, --digest VAL'},
                 {'help': 'Filter runs that are still running.',
                  'term': '-Sr, --running / --not-running'},
                 {'help': 'Filter completed runs.',
                  'term': '-Sc, --completed / --not-completed'},
                 {'help': 'Filter runs that exited with an error.',
                  'term': '-Se, --error / --not-error'},
                 {'help': 'Filter runs terminated by the user.',
                  'term': '-St, --terminated / --not-terminated'},
                 {'help': 'Filter pending runs.',
                  'term': '-Sp, --pending / --not-pending'},
                 {'help': 'Filter staged runs.',
                  'term': '-Ss, --staged / --not-staged'},
                 {'help': 'List runs on REMOTE rather than local runs.',
                  'term': '-r, --remote REMOTE'},
                 {'help': 'Show this message and exit.', 'term': '--help'}],
     'usage': {'args': '[OPTIONS] COMMAND [ARGS]...', 'prog': 'guild runs'},
     'version': '...'}
