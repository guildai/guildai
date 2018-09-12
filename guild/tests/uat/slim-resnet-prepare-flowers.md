# slim.resnet prepare flowers

Direct output to /dev/null to avoid freezing (I believe related to
rapid stdout updates from the processing progress).

TODO: reinstate or otherwise modify when packages are fixed

    >> run("guild run flowers:prepare -y --no-gpus > /dev/null",
    ...     timeout=300)
    Limiting available GPUs (CUDA_VISIBLE_DEVICES) to: <none>
    Resolving slim/models-lib dependency
    ...
    <exit 0>

List the prepared flowers datasets:

TODO: reinstate or otherwise modify when packages are fixed

    >> run("guild runs list -o flowers")
    [0:...]  gpkg.slim.datasets/slim-flowers:prepare  ... ...  completed
    <exit 0>
