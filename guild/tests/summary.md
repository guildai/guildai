# Summary utils

    >>> from guild import summary

    >>> from guild import tfevent
    >>> tfevent._ensure_tb_logging_patched()

## Output scalars

### Config and compiled patterns

Create a function to compile and print patterns from output scalar
config.

    >>> import logging

    >>> def compiled(config):
    ...     with LogCapture(log_level=logging.INFO) as logs:
    ...         out = summary.OutputScalars(config, None)
    ...     logs.print_all()
    ...     out.print_patterns()

Empty list:

    >>> compiled([])

Invalid config:

    >>> compiled({})
    Traceback (most recent call last):
    TypeError: invalid output scalar config: {}

    >>> compiled("not allowed")
    Traceback (most recent call last):
    TypeError: invalid output scalar config: 'not allowed'

Maps:

    >>> compiled([{"loss": "loss: (\S+)"}]) # doctest: -NORMALIZE_PATHS
    loss: loss: (\S+)

    >>> compiled([{"step": "step=(\d+)", "loss": "loss=(\d+\.\d+)"}]) # doctest: -NORMALIZE_PATHS
    ???loss: loss=(\d+\.\d+)
    step: step=(\d+)

Two group (key and value):

    >>> compiled(["(\S+): ([+-]?\d+\.\d+)"]) # doctest: -NORMALIZE_PATHS
    ???None: (\S+): ([+-]?\d+\.\d+)

Named groups:

    >>> compiled([
    ...     "Epochs (?P<step>\d+): "
    ...     "loss=(?P<loss>\S+) "
    ...     "acc=(?P<acc>\S+) "
    ...     "val_acc=(?P<val_acc>\S+)"]) # doctest: -NORMALIZE_PATHS
    None: Epochs (?P<step>\d+):
          loss=(?P<loss>\S+)
          acc=(?P<acc>\S+)
          val_acc=(?P<val_acc>\S+)

### Patterns

Function to test patterns:

    >>> def test_p(p, s):
    ...     with LogCapture() as logs:
    ...         compiled = summary._compile_patterns(f"^{p}$", None)
    ...     logs.print_all()
    ...     if not compiled:
    ...         return False
    ...     # _compile_patterns has an odd interface that
    ...     # returns a list of compiled patterns when it
    ...     # really should return None or a single compiled
    ...     # pattern. This is an alleged convenience in the
    ...     # implementation as the implementation works with
    ...     # lists of patterns.
    ...     return compiled[0][1].match(s) is not None

Test various patterns.

    >>> test_p("", "")
    True

    >>> test_p("foo", "")
    False

    >>> test_p("foo", "foo")
    True

    >>> test_p(r"loss: \d", "loss: 123")
    False

    >>> test_p(r"loss: \d+", "loss: 123")
    True

    >>> test_p(r"loss: \d", "loss: bar")
    False

    >>> test_p(r"loss: (\d\d)", "loss: 123")
    False

    >>> test_p(r"loss: (\d\d\d)", "loss: 123")
    True

Guild supports the following aliases:

    >>> summary.ALIASES  # doctest: -NORMALIZE_PATHS
    [(re.compile('\\\\key'), '...'),
     (re.compile('\\\\value'), '...'),
     (re.compile('\\\\step'), '...')]

Test various examples for `\value` alias:

    >>> examples = [
    ...     # Inf / NaN
    ...     "inf",
    ...     "nan",
    ...     "NaN",
    ...     "INF",
    ...     "+inf",
    ...     "-inf",
    ...
    ...     # Floats
    ...     ".12",
    ...     "-.12",
    ...     "+.12",
    ...     "16.",
    ...     "1.2",
    ...     "-0.3",
    ...     "+0.3",
    ...
    ...     # Exponents
    ...     "1e6",
    ...     "1.7e-9",
    ...     "1.7e+9",
    ...     "-1.7e-9",
    ...     "-1.7e+9",
    ...     "+1.7e-9",
    ...     "-1.7e+9",
    ...     ".123e3",
    ...     "-.123e3",
    ...     "+.123e3",
    ...
    ...     # Ints
    ...     "1",
    ...     "12",
    ...     "-12",
    ...     "+12",
    ...
    ...     # Invalid values
    ...     "e6",
    ...     "tree",
    ...     "1t7",
    ...     ".1.7e+9",
    ... ]

    >>> for s in examples:  # doctest: +REPORT_UDIFF
    ...     result = test_p(r"\value", s)
    ...     print(f"{s}: {result}")
    inf: True
    nan: True
    NaN: True
    INF: True
    +inf: True
    -inf: True
    .12: True
    -.12: True
    +.12: True
    16.: True
    1.2: True
    -0.3: True
    +0.3: True
    1e6: True
    1.7e-9: True
    1.7e+9: True
    -1.7e-9: True
    -1.7e+9: True
    +1.7e-9: True
    -1.7e+9: True
    .123e3: True
    -.123e3: True
    +.123e3: True
    1: True
    12: True
    -12: True
    +12: True
    e6: True
    tree: False
    1t7: False
    .1.7e+9: False

Note that Guild incorrectly matches `e6` above - while incorrect we
accept this to keep the regular pattern for `\value` somewhat sane and
also match patterns like `.123`, which are reasonable float
representations in Python.

### Processing output

Create a function to process output lines according to output scalar
config. Prints tag, value, and step associated with processed output.

    >>> def match(config, lines):
    ...     output_dir = mkdtemp()
    ...     with LogCapture() as logs:
    ...         out = summary.OutputScalars(config, output_dir)
    ...         for line in lines:
    ...             out.write(line + "\n")
    ...         out.close()
    ...     logs.print_all()
    ...     reader = tfevent.ScalarReader(output_dir)
    ...     for tag, val, step in reader:
    ...         print(tag, val, step)

Empty config:

    >>> match([], [])

Config capturing loss for a single step:

    >>> match([{"loss": r"(\value)"}], ["1"])
    loss 1.0 0

    >>> match([{"loss": r"loss=(\value)"}], ["loss=2"])
    loss 2.0 0

    >>> match([r"(\key)... (\value)"], ["loss... 2"])
    loss 2.0 0

Capturing loss for multiple steps (step is not captured and is
therefore always `0`):

    >>> match([{"loss": r"(\value)"}], ["1", "2", "3"])
    loss 1.0 0
    loss 2.0 0
    loss 3.0 0

Capturing loss for multiple steps:

    >>> match([r"\key: \value \((?P<step>\step)\)", r"(\key): (\value)"],
    ... ["loss: 1 (10)",
    ...  "loss: 2 (20)",
    ...  "loss: 3 (30)"])
    loss 1.0 10
    loss 2.0 20
    loss 3.0 30

Capturing loss and acc for multiple steps:

    >>> match([r"\key: +\value \((?P<step>\step)\)", r"(\key): +(\value)"],
    ... ["loss: 1 (10)",
    ...  "acc:  2 (10)",
    ...  "loss: 3 (20)",
    ...  "acc:  4 (20)",
    ...  "loss: 5 (30)",
    ...  "acc:  6 (30)"])
    loss 1.0 10
    acc 2.0 10
    loss 3.0 20
    acc 4.0 20
    loss 5.0 30
    acc 6.0 30

Config capturing step, loss, and acc for two steps:

    >>> match([{
    ...     "step": "step (\d+):",
    ...     "loss": "loss: (\S+)",
    ...     "acc": "acc: (\S+)",
    ... }],
    ... ["Training...",
    ...  "step 1:",
    ...  "loss: 1.123 - acc: 0.134",
    ...  "step 2:",
    ...  "loss: 0.132 - acc: 0.456"])
    ???acc 0.13400... 1
    loss 1.12300... 1
    acc 0.45600... 2
    loss 0.13... 2

Alternative map config:

    >>> match([{
    ...     "step": "Epoch (\S+):",
    ...     "loss": "loss=(\S+)",
    ...     "s_val": "s_val=(\S+)",
    ...     "x": "x=(\S+)",
    ...     "mAP": "mAP=(\S+)",
    ... }],
    ... ["Epoch 1: loss=1.0 s_val=2 x=3 mAP=4.123",
    ...  "Epoch 2: loss=2.0 s_val=3 x=4 mAP=5.234",
    ...  "Epoch 3: loss=3.0 s_val=4 x=4 mAP=6.4567890123456"])
    ???loss 1.0 1
    mAP 4.123000... 1
    s_val 2.0 1
    x 3.0 1
    loss 2.0 2
    mAP 5.234000... 2
    s_val 3.0 2
    x 4.0 2
    loss 3.0 3
    mAP 6.456789... 3
    s_val 4.0 3
    x 4.0 3

Named groups:

    >>> match(["Epoch (?P<step>\S+): "
    ...        "loss=(?P<loss>\S+) "
    ...        "s_val=(?P<s_val>\S+) "
    ...        "x=(?P<x>\S+) "
    ...         "mAP=(?P<mAP>\S+)"],
    ... ["Epoch 1: loss=1.0 s_val=2 x=3 mAP=4.123",
    ...  "Epoch 2: loss=2.0 s_val=3 x=4 mAP=5.234",
    ...  "Epoch 3: loss=3.0 s_val=4 x=4 mAP=6.4567890123456"])
    ???loss 1.0 1
    mAP 4.123000... 1
    s_val 2.0 1
    x 3.0 1
    loss 2.0 2
    mAP 5.234000... 2
    s_val 3.0 2
    x 4.0 2
    loss 3.0 3
    mAP 6.456789... 3
    s_val 4.0 3
    x 4.0 3

Named group - error in config (using pipe as literal but it's applied
as OR):

    >>> match(["iter (?P<step>\\step) | loss: (?P<loss>\\value)",
    ...       {"score": "Total loss: (\\value)"}],
    ... ["iter 0 | loss: 0.6",
    ...  "iter 1 | loss: 0.4",
    ...  "Total loss: 1.1"])
    ???loss 0.600... 0
    loss 0.400... 1
    loss 1.100... 1
    score 1.100... 1

With correction:

    >>> match(["iter (?P<step>\\step) \\| loss: (?P<loss>\\value)",
    ...       {"score": "Total loss: (\\value)"}],
    ... ["iter 0 | loss: 0.6",
    ...  "iter 1 | loss: 0.4",
    ...  "Total loss: 1.1"])
    ???loss 0.600... 0
    loss 0.400... 1
    score 1.100... 1

Two group patterns:

    >>> match(["(\S+):\s+([\d\.eE\-+]+)"],
    ...  ["loss: 1.123",
    ...   "acc: 0.456",
    ...   "val_acc: 1.1e-3",
    ...   "foo: bar"])
    ???loss 1.12300... 0
    acc 0.45600... 0
    val_acc 0.001... 0

Special groupdict convention for controlling order of key and value:

    >>> match(["(?P<_val>[+-]?[\d\.]+) \((?P<_key>\S+)\)"],
    ...  ["1.123 (loss)",
    ...   "0.456 (acc)",
    ...   "0.567 (val_acc)"])
    ???loss 1.12300... 0
    acc 0.45600... 0
    val_acc 0.56... 0

Multiple matches per line:

    >>> match([{"x": "x=(\d+)"}],
    ...  ["x=1 y=1 - x=2 y=2 - x=3 y=3"])
    ???x 3.0 0

    >>> match(["(\w+)=(\d+)"],
    ...  ["x=1 y=1 - x=2 y=2 - x=3 y=3"])
    ???x 3.0 0
    y 3.0 0

    >>> match([r"x=(?P<x2>\d+)", "y=(?P<y2>\d+)"],
    ...  ["x=1 y=1 - x=2 y=2 - x=3 y=3"])
    ???x2 3.0 0
    y2 3.0 0

## Logging scalars

The tests below use the `summary` sample project.

    >>> use_project("summary")

### Repeating lines

`repeating_lines.py` prints scalar blocks with a 'step' header:

    >>> run("guild run repeating_lines.py -y")
    step: 1
    x: 1
    step: 2
    x: 2
    step: 3
    x: 3
    x: 4

    >>> run("guild tensorboard --export-scalars - 1")
    run,path,tag,value,step
    ...,.guild,x,1.0,1
    ...,.guild,x,2.0,2
    ...,.guild,x,3.0,3
    ...,.guild,x,4.0,3

`repeating_lines2.py` prints scalars inline with the step specified
next to each scalar:

    >>> run("guild run repeating_lines2.py -y")
    x: 1 (step 1)
    x: 3 (3)
    x: 2 (step 2)
    x: 4
    x: 5 (5)
    x: 6 (not a step)

Note the steps order is 1, 3, 2... This is intentional to show that
Guild captures the step for associated with each scalar. In this
example, the scalar value `4` is associated with step `2`. From the
user standpoint is a bug - the step is accidentally omited. Guild's
behavior, however, is by design: Guild uses the last logged step,
regardless of whether it is lower than previously logged steps.

    >>> run("guild tensorboard --export-scalars - 1")
    run,path,tag,value,step
    ...,.guild,x,1.0,1
    ...,.guild,x,3.0,3
    ...,.guild,x,2.0,2
    ...,.guild,x,4.0,2
    ...,.guild,x,5.0,5
    ...,.guild,x,6.0,5

## Status lookup

Below is the mapping of Guild run status to hparam status.

As a baseline, here are the int values for each of the hparam
statuses.

    >>> from tensorboard.plugins.hparams import api_pb2

    >>> api_pb2.Status.Value("STATUS_SUCCESS")
    1

    >>> api_pb2.Status.Value("STATUS_FAILURE")
    2

    >>> api_pb2.Status.Value("STATUS_RUNNING")
    3

    >>> api_pb2.Status.Value("STATUS_UNKNOWN")
    0

And the status values for Guild statuses:

    >>> summary._Status("terminated")
    1

    >>> summary._Status("completed")
    1

    >>> summary._Status("error")
    2

    >>> summary._Status("running")
    3

    >>> summary._Status("pending")
    0

    >>> summary._Status("some-other-thing")
    0
