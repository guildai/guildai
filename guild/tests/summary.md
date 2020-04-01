# Summary utils

    >>> from guild import summary

    >>> from guild import tfevent
    >>> tfevent._ensure_tb_logging_patched()

## Output scalars

### Config and compiled patterns

Helper function to compile and print patterns from config:

    >>> def compiled(config):
    ...     with LogCapture() as logs:
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
    loss: loss=(\d+\.\d+)
    step: step=(\d+)

Two group (key and value):

    >>> compiled(["(\S+): ([+-]?\d+\.\d+)"]) # doctest: -NORMALIZE_PATHS
    None: (\S+): ([+-]?\d+\.\d+)

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

### Processing output

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

Typical map config:

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
    acc 0.13400... 1
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
    loss 1.0 1
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
    loss 1.0 1
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
    loss 0.600... 0
    loss 0.400... 1
    loss 1.100... 1
    score 1.100... 1

With correction:

    >>> match(["iter (?P<step>\\step) \\| loss: (?P<loss>\\value)",
    ...       {"score": "Total loss: (\\value)"}],
    ... ["iter 0 | loss: 0.6",
    ...  "iter 1 | loss: 0.4",
    ...  "Total loss: 1.1"])
    loss 0.600... 0
    loss 0.400... 1
    score 1.100... 1

Two group patterns:

    >>> match(["(\S+):\s+([\d\.eE\-+]+)"],
    ...  ["loss: 1.123",
    ...   "acc: 0.456",
    ...   "val_acc: 1.1e-3",
    ...   "foo: bar"])
    loss 1.12300... 0
    acc 0.45600... 0
    val_acc 0.001... 0

Special groupdict convention for controlling order of key and value:

    >>> match(["(?P<_val>[+-]?[\d\.]+) \((?P<_key>\S+)\)"],
    ...  ["1.123 (loss)",
    ...   "0.456 (acc)",
    ...   "0.567 (val_acc)"])
    loss 1.12300... 0
    acc 0.45600... 0
    val_acc 0.56... 0

Multiple matches per line:

    >>> match([{"x": "x=(\d+)"}],
    ...  ["x=1 y=1 - x=2 y=2 - x=3 y=3"])
    x 3.0 0

    >>> match(["(\w+)=(\d+)"],
    ...  ["x=1 y=1 - x=2 y=2 - x=3 y=3"])
    x 3.0 0
    y 3.0 0

    >>> match([r"x=(?P<x2>\d+)", "y=(?P<y2>\d+)"],
    ...  ["x=1 y=1 - x=2 y=2 - x=3 y=3"])
    x2 3.0 0
    y2 3.0 0

## Logging scalars

The tests below use the `summary` sample project.

    >>> project = Project(sample("projects/summary"))

### Repeating lines

    >>> project.run("repeating_lines.py")
    step: 1
    x: 1
    step: 2
    x: 2
    step: 3
    x: 3
    x: 4

    >>> last_run = project.list_runs()[0]
    >>> scalars = project.scalars(last_run)
    >>> pprint(scalars) # doctest: +REPORT_UDIFF
    [{'avg_val': 2.5,
      'count': 4,
      'first_step': 1,
      'first_val': 1.0,
      'last_step': 3,
      'last_val': 4.0,
      'max_step': 3,
      'max_val': 4.0,
      'min_step': 1,
      'min_val': 1.0,
      'prefix': '.guild',
      'run': '...',
      'tag': 'x',
      'total': 10.0}]

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
