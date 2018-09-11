# slim.resnet prepare flowers

Direct output to /dev/null to avoid freezing (I believe related to
rapid stdout updates from the processing progress).

    >>> run("guild run flowers:prepare -y --no-gpus > /dev/null",
    ...     timeout=300)
    Limiting available GPUs (CUDA_VISIBLE_DEVICES) to: <none>
    Resolving slim/models-lib dependency
    ...
    <exit 0>

List the prepared flowers datasets:

    >>> run("guild runs list -o flowers")
    [0:...]  slim.datasets/slim-flowers:prepare  ... ...  completed
    <exit 0>
