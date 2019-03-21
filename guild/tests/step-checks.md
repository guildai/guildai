# Step checks

Steps can be used to check run results.

For these tests we'll use the `step-checks` project.

    >>> project = Project(sample("projects", "step-checks"))

The project has two public operations and a number of private
operation (i.e. operations starting with `_`).

    >>> gf = guildfile.from_dir(project.cwd)

    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef '_test-all'>,
     <guild.guildfile.OpDef '_test-fail-1'>,
     <guild.guildfile.OpDef '_test-file-1'>,
     <guild.guildfile.OpDef '_test-output-1'>,
     <guild.guildfile.OpDef '_test-output-2'>,
     <guild.guildfile.OpDef 'gen-files'>,
     <guild.guildfile.OpDef 'gen-output'>]

Here's a helper for printing op steps:

    >>> def print_steps(op):
    ...     pprint(gf.default_model.get_operation(op).steps)

As a convention, tests in Guild are implemented as private operations
and use `steps` attrs.

Here's the `_test-output-1` operation steps:

    >>> print_steps("_test-output-1")
    [{'expect': [{'output': 'hi'}], 'run': 'gen-output'}]

We can see that there is one step, which runs `gen-output` and asserts
that the generated output should contain the string 'hi'.

Let's run the operation:

    >>> project.run("_test-output-1")
    INFO: [guild] running gen-output: gen-output
    hi
    INFO: [guild] checking run ... output for 'hi'
    INFO: [guild] 1 of 1 checks passed

Here's `_test-output-2`:

    >>> print_steps("_test-output-2")
    [{'expect': [{'output': 'hello'}, {'output': 'car'}],
      'run': "gen-output msg='hello car'"}]

This test checks for two outputs: 'hello' and 'car'. Let's run it:

    >>> project.run("_test-output-2")
    INFO: [guild] running gen-output: gen-output 'msg=hello car'
    hello car
    INFO: [guild] checking run ... output for 'hello'
    INFO: [guild] checking run ... output for 'car'
    INFO: [guild] 2 of 2 checks passed

`_test-file-1`:

    >>> print_steps("_test-file-1")
    [{'expect': [{'contains': 'hello bus', 'file': 'file-1'},
                 {'file': 'sample.txt'}],
      'run': "gen-files count=1 msg='hello bus'"}]

And its result:

    >>> project.run("_test-file-1")
    INFO: [guild] running gen-files: gen-files count=1 'msg=hello bus'
    Resolving file:sample.txt dependency
    INFO: [guild] checking run ... files 'file-1'
    INFO: [guild] checking run ... file file-1 for 'hello bus'
    INFO: [guild] checking run ... files 'sample.txt'
    INFO: [guild] 2 of 2 checks passed

One of the tests is designed to fail. Let's look at `_test-fail-1`:

    >>> print_steps("_test-fail-1")
    [{'expect': [{'output': 'bye'}], 'run': 'gen-output'}]

When we run it:

    >>> project.run("_test-fail-1")
    INFO: [guild] running gen-output: gen-output
    hi
    INFO: [guild] checking run ... output for 'bye'
    ERROR: [guild] check failed: could not find pattern 'bye' in run ... output
    INFO: [guild] 0 of 1 checks passed
    ERROR: [guild] 1 check(s) failed - see above for details
    guild: stopping because a check failed
    <exit 3>

Checks can be aggregated by simply running them as steps. `_test-all`
does this:

    >>> print_steps("_test-all")
    ['_test-output-1', '_test-output-2', '_test-file-1', '_test-fail-1']

    >>> project.run("_test-all")
    INFO: [guild] running _test-output-1: _test-output-1
    INFO: [guild] running gen-output: gen-output
    hi
    INFO: [guild] checking run ... output for 'hi'
    INFO: [guild] 1 of 1 checks passed
    INFO: [guild] running _test-output-2: _test-output-2
    INFO: [guild] running gen-output: gen-output 'msg=hello car'
    hello car
    INFO: [guild] checking run ... output for 'hello'
    INFO: [guild] checking run ... output for 'car'
    INFO: [guild] 2 of 2 checks passed
    INFO: [guild] running _test-file-1: _test-file-1
    INFO: [guild] running gen-files: gen-files count=1 'msg=hello bus'
    Resolving file:sample.txt dependency
    INFO: [guild] checking run ... files 'file-1'
    INFO: [guild] checking run ... file file-1 for 'hello bus'
    INFO: [guild] checking run ... files 'sample.txt'
    INFO: [guild] 2 of 2 checks passed
    INFO: [guild] running _test-fail-1: _test-fail-1
    INFO: [guild] running gen-output: gen-output
    hi
    INFO: [guild] checking run ... output for 'bye'
    ERROR: [guild] check failed: could not find pattern 'bye' in run ... output
    INFO: [guild] 0 of 1 checks passed
    ERROR: [guild] 1 check(s) failed - see above for details
    guild: stopping because a check failed
    <exit 3>
