# Custom run attrs example

The `attrs` example illustrates custom run attributes.

    >>> cd(example("attrs"))

The sample project requires `tensorboardX`.

    >>> quiet("pip install tensorboardX")

## Logging attributes explicitly

Run various scripts that log custom attributes.

Log using Guild's summary support:

    >>> run("guild run logged_guild_summary.py -y")
    <exit 0>

    >>> run("guild runs info")
    id: ...
    operation: logged_guild_summary.py
    ...
    scalars:
      loss: 0.010000 (step 4)
      train#loss: 0.030000 (step 4)
    attributes:
      custom: 123
      model: cnn
      train#model: cnn-2

Test various examples using `--test-output-attrs`.

    >>> run("echo 'foo: 1.123' | guild run logged_guild_summary.py --test-output-attrs -")
    foo: 1.123
      '^([_a-zA-Z]\\S*):\\s+(\\S+)$': [('foo', '1.123')] (foo=1.123)

    >>> run("echo 'foo: bar' | guild run logged_guild_summary.py --test-output-attrs -")
    foo: bar
      '^([_a-zA-Z]\\S*):\\s+(\\S+)$': [('foo', 'bar')] (foo=bar)

By default Guild doesn't capture attrs with spaces.

    >>> run("echo 'foo: bar baz' | guild run logged_guild_summary.py --test-output-attrs -")
    foo: bar baz
      '^([_a-zA-Z]\\S*):\\s+(\\S+)$': <no matches>

Log using tensorboardX:

    >>> run("guild run logged_tbx_summary.py -y")
    <exit 0>

    >>> run("guild runs info")
    id: ...
    operation: logged_tbx_summary.py
    ...
    scalars:
      loss: 0.010000 (step 4)
    attributes:
      model: cnn
    <exit 0>

## Output attributes

    >>> run("guild run output.py -y")
    model: cnn
    loss: 0.123
    acc: 0.654
    <exit 0>

    >>> run("guild runs info")
    id: ...
    operation: output.py
    ...
    scalars:
      acc: 0.654000 (step 0)
      loss: 0.123000 (step 0)
    attributes:
      model: cnn

## Guild file defined ops

Output script with controlled scalars and attributes.

    >>> run("guild run output -y")
    model: cnn
    loss: 0.123
    acc: 0.654

    >>> run("guild runs info")
    id: ...
    operation: output
    ...
    scalars:
      acc: 0.654000 (step 0)
      loss: 0.123000 (step 0)
    attributes:
      model: cnn

Test output attrs.

    >>> run("echo 'foo: 1.213' | guild run output --test-output-attrs -")
    foo: 1.213
      'model: (.*)': <no matches>

    >>> run("echo 'model: llm' | guild run output --test-output-attrs -")
    model: llm
      'model: (.*)': [('llm',)] (model=llm)

    >>> run("echo 'model: a file model' | guild run output --test-output-attrs -")
    model: a file model
      'model: (.*)': [('a file model',)] (model=a file model)
