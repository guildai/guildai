# Runs - part 2

This is a continuation of [Part 1](runs-1.md).

We continue examining the runs in samples/runs.

    >>> runs_dir = sample("runs")
    >>> guild_home = os.path.dirname(runs_dir)

We use gapi to for our tests:

    >>> from guild import _api as gapi
    >>> runs_list = lambda **kw: gapi.runs_list(guild_home=guild_home, **kw)

A helper to print runs:

    >>> def print_runs(runs):
    ...   for run in runs:
    ...     print(run.short_id, run.opref.to_opspec(), run.status)

Runs list:

    >>> print_runs(runs_list())
    ???42803252 mnist:evaluate completed
    7d145216 mnist:train error
    360192fd mnist:train pending

Filtered by 'train' operation:

    >>> print_runs(runs_list(ops=["train"]))
    ???7d145216 mnist:train error
    360192fd mnist:train pending

Filter by partial op name 'ain' does not match:

    >>> print_runs(runs_list(ops=["ain"]))

    >>> print_runs(runs_list(ops=["tra"]))

We can use a wildcard pattern however:

    >>> print_runs(runs_list(ops=["*ain"]))
    ???7d145216 mnist:train error
    360192fd mnist:train pending

    >>> print_runs(runs_list(ops=["tra*"]))
    ???7d145216 mnist:train error
    360192fd mnist:train pending

Use a spec containing model:

    >>> print_runs(runs_list(ops=["mnist:train"]))
    7d145216 mnist:train error
    360192fd mnist:train pending

Show all ops for model:

    >>> print_runs(runs_list(ops=["mnist:*"]))
    42803252 mnist:evaluate completed
    7d145216 mnist:train error
    360192fd mnist:train pending

Match the wrong model:

    >>> print_runs(runs_list(ops=["mnist2:*"]))

Use a wildcard to match everything:

    >>> print_runs(runs_list(ops=["*"]))
    ???42803252 mnist:evaluate completed
    7d145216 mnist:train error
    360192fd mnist:train pending

Use a wildcard to match the model:

    >>> print_runs(runs_list(ops=["*:evaluate"]))
    42803252 mnist:evaluate completed

    >>> print_runs(runs_list(ops=["mni*:evaluate"]))
    42803252 mnist:evaluate completed

    >>> print_runs(runs_list(ops=["*ist:evaluate"]))
    42803252 mnist:evaluate completed

Filter by starts with 'mnist':

    >>> print_runs(runs_list(ops=["^mnist:"]))
    42803252 mnist:evaluate completed
    7d145216 mnist:train error
    360192fd mnist:train pending

Filter to select mnist train or evaluate:

    >>> print_runs(runs_list(ops=["^mnist:(train|evaluate)"]))
    42803252 mnist:evaluate completed
    7d145216 mnist:train error
    360192fd mnist:train pending

Filter to select evaluate or test:

    >>> print_runs(runs_list(ops=[":(evaluate|test)$"]))
    42803252 mnist:evaluate completed

Filtered by 'evaluate' operation:

    >>> print_runs(runs_list(ops=["evaluate"]))
    42803252 mnist:evaluate completed

Filtered by completed various status:

    >>> print_runs(runs_list(completed=True))
    ???42803252 mnist:evaluate completed

    >>> print_runs(runs_list(error=True))
    ???7d145216 mnist:train error

    >>> print_runs(runs_list(pending=True))
    360192fd mnist:train pending

    >>> print_runs(runs_list(pending=True, error=True))
    ???7d145216 mnist:train error
    360192fd mnist:train pending

    >>> runs_list(foobar=True)
    Traceback (most recent call last):
    TypeError: runs_list() got an unexpected keyword argument 'foobar'

## Run env

Run env can be specified using the operation `env` attribute.

Here's a project demonstrating this.

    >>> p = Project(sample("projects", "run-env"))

    >>> gf = guildfile.for_dir(p.cwd)

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'all-env'>, <guild.guildfile.OpDef 'hide-bar'>]

### All env

The `all-env` operation saves all env.

    >>> all_env = gf.default_model.get_operation("all-env")

    >>> pprint(all_env.env)
    {'bar': 'hello', 'foo': 123}

    >>> print(all_env.env_secrets)
    None

Run the op:

    >>> p.run("all-env")
    123
    hello

Check the run env attr:

    >>> run = p.list_runs()[0]
    >>> env = run.get("env")

    >>> env["foo"]
    '123'

    >>> env["bar"]
    'hello'

### Secret env

The `hide-bar` operation saves all env except `bar`, which is
considered a secret.

    >>> hide_bar = gf.default_model.get_operation("hide-bar")

    >>> pprint(hide_bar.env)
    {'bar': 'hi', 'foo': 456}

    >>> print(hide_bar.env_secrets)
    ['bar']

Run the op:

    >>> p.run("hide-bar")
    456
    hi

Check the run env attr:

    >>> run = p.list_runs()[0]
    >>> env = run.get("env")

    >>> env["foo"]
    '456'

Note that `bar` is not saved to env:

    >>> env["bar"]
    Traceback (most recent call last):
    KeyError: 'bar'
