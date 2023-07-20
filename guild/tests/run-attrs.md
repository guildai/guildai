# Run attrs

Custom attributes can be defined for an operation using the
`run-attrs` op attr. The `run-attrs` sample project illustrates.

    >>> use_project("run-attrs")

## Custom attributes

Guild prohibits use of core attributes.

    >>> run("guild run op -y")  # doctest: +REPORT_UDIFF
    WARNING: Invalid run attribute 'cmd' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'deps' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'env' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'exit_status' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'flags' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'host' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'id' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'initialized' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'label' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'op' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'pip_freeze' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'platform' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'plugins' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'random_seed' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'run_params' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'sourcecode_digest' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'started' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'stopped' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'user' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'user_flags' (reserved attribute) - ignoring
    WARNING: Invalid run attribute 'vcs_commit' (reserved attribute) - ignoring
    <exit 0>

Non-core attributes, however, are written.

    >>> run("guild runs info")
    id: ...
    operation: op
    from: .../samples/projects/run-attrs/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label:
    sourcecode_digest: ...
    vcs_commit:...
    run_dir: ...
    command: ...
    exit_status: 0
    pid:
    tags:
    flags:
    scalars:
    attributes:
      another-custom: baz
      custom: bar
      yet-another-custom:
        a: A
        b: 123
        c: 1.234
    <exit 0>

## Encoding of `[ynYN]` keys

When writing attributes, Guild applies quotes to single character
boolean values as per the YAML spec to ensure that external
applications can read run attributes without special handling for
these unquoted chars.

    >>> run("guild run boolean-chars -y")
    <exit 0>

    >>> run("guild runs info")
    id: ...
    operation: boolean-chars
    ...
    flags:
      N: 44
      Y: 33
      a: 55
      n: 22
      y: 11
      z: 66
    scalars:
    attributes:
      custom:
        N: 4
        Y: 3
        a: 5
        n: 2
        y: 1
        z: 6

    >>> run("guild cat -p .guild/attrs/opdef_attrs")
    custom:
      'N': 4
      'Y': 3
      a: 5
      'n': 2
      'y': 1
      z: 6

    >>> run("guild cat -p .guild/attrs/flags")
    'N': 44
    'Y': 33
    a: 55
    'n': 22
    'y': 11
    z: 66

## Logged attributes

The `logged` operation logs various attributes using text summaries as
well as defines a run attribute in the Guild file.

    >>> run("guild run logged -y")
    <exit 0>

    >>> run("guild runs info")
    id: ...
    operation: logged
    ...
    attributes:
      logged-1: green
      logged-2: '{"numbers": [1, 3, 5], "color": "blue"}'
      opdef-attr: red
    <exit 0>

The `logged-core` operation logs core attributes `id` and
`label`. Guild ignores these logged attributes.

    >>> cat("logged_core.py")
    from guild import summary
    <BLANKLINE>
    attrs = summary.SummaryWriter(".", filename_suffix=".attrs")
    attrs.add_text("id", "bbb")
    attrs.add_text("label", "Trying to log a label")

    >>> run("guild run logged-core --run-id aaa --label 'True label' -y")
    <exit 0>

    >>> run("guild runs info")
    id: aaa
    operation: logged-core
    ...
    label: True label
    ...
    attributes:
      custom-id: This attr is okay
      custom-label: This attr is also okay

## Output attributes

Guild can capture attributes as output for a run.

The default rules for output captures follow the pattern used by
scalars, but apply to text values as well we numbers. By default,
values containing spaces are not matched. This is to avoid
accidentally matching log-style output.

Output scalar patterns are applied first and take precedence over
matching attributes.

The `output.py` script in the sample project demonstrates a common
case.

    >>> run("guild run output.py -y")
    model: cnn
    xxx: will not be captured with default rules
    loss: 0.123
    acc: 0.765
    loss: 0.012
    acc: 0.876

    >>> run("guild runs info")
    id: ...
    operation: output.py
    ...
    scalars:
      acc: 0.876000 (step 1)
      loss: 0.012000 (step 1)
    attributes:
      model: cnn

The `output-2` operation, defined in the Guild file, runs the same
operation, but disables output scalars and explicitly matches the
otherwise ignored `xxx` attribute.

    >>> run("guild run output-2 -y")
    model: cnn
    xxx: will not be captured with default rules
    loss: 0.123
    acc: 0.765
    loss: 0.012
    acc: 0.876

    >>> run("guild runs info")
    id: ...
    operation: output-2
    ...
    scalars:
    attributes:
      xxx: will not be captured with default rules
