# Guild View

Use the `view` sample project.

    >>> project = Project(sample("projects", "view"))

Generate a run.

    >>> project.run("op.py", comment="sample run for view", tags=["blue", "green"])

    >>> project.print_runs()
    op.py

Use hidden `--test-runs-data` to get JSON-encoded runs data from view
command.

    >>> import subprocess
    >>> env = dict(os.environ)
    >>> env["PYTHONPATH"] = os.path.pathsep.join(sys.path)
    >>> runs_data_output = subprocess.check_output([
    ...         sys.executable,
    ...         "-m",
    ...         "guild.main_bootstrap",
    ...         "-H",
    ...         project.guild_home,
    ...         "view",
    ...         "--test-runs-data",
    ...     ],
    ...     cwd=project.cwd,
    ...     env=env,
    ... )

    >>> import json
    >>> runs_data = json.loads(runs_data_output.decode())

Number of runs:

    >>> len(runs_data)
    1

Available run data:

    >>> run_data = runs_data[0]

    >>> pprint(sorted(run_data.keys()))
    ['command',
     'comments',
     'deps',
     'env',
     'exitStatus',
     'files',
     'flags',
     'id',
     'label',
     'opModel',
     'opName',
     'operation',
     'otherAttrs',
     'path',
     'scalars',
     'shortId',
     'started',
     'status',
     'stopped',
     'tags',
     'time']

Scalars:

    >>> pprint(run_data["scalars"])
    [{'avg_val': 'Infinity',
      'count': 3,
      'first_step': 1,
      'first_val': 1.123000...,
      'last_step': 3,
      'last_val': 'Infinity',
      'max_step': 3,
      'max_val': 'Infinity',
      'min_step': 1,
      'min_val': 1.123000...,
      'prefix': '',
      'run': '...',
      'tag': 'x',
      'total': 'Infinity'},
     {'avg_val': '-Infinity',
      'count': 3,
      'first_step': 1,
      'first_val': '-Infinity',
      'last_step': 3,
      'last_val': 2.0,
      'max_step': 3,
      'max_val': 2.0,
      'min_step': 1,
      'min_val': '-Infinity',
      'prefix': '',
      'run': '...',
      'tag': 'y',
      'total': '-Infinity'},
     {'avg_val': None,
      'count': 1,
      'first_step': 1,
      'first_val': None,
      'last_step': 1,
      'last_val': None,
      'max_step': 1,
      'max_val': None,
      'min_step': 1,
      'min_val': None,
      'prefix': '',
      'run': '...',
      'tag': 'z',
      'total': None}]

Comments:

    >>> pprint(run_data["comments"])
    [{'body': 'sample run for view',
      'host': '...',
      'time': ...,
      'user': '...'}]

Tags:

    >>> pprint(run_data["tags"])
    'blue, green'
