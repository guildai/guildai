skip-windows: yes

# Summary utils

    >>> from guild import summary

    >>> from guild import tfevent
    >>> tfevent.ensure_tf_logging_patched()

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

    >>> compiled([{"loss": "loss: (\S+)"}])
    loss: loss: (\S+)

    >>> compiled([{"step": "step=(\d+)", "loss": "loss=(\d+\.\d+)"}])
    loss: loss=(\d+\.\d+)
    step: step=(\d+)

Two group (key and value):

    >>> compiled(["(\S+): ([+-]?\d+\.\d+)"])
    None: (\S+): ([+-]?\d+\.\d+)

Named groups:

    >>> compiled([
    ...     "Epochs (?P<step>\d+): "
    ...     "loss=(?P<loss>\S+) "
    ...     "acc=(?P<acc>\S+) "
    ...     "val_acc=(?P<val_acc>\S+)"])
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
