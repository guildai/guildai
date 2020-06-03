# Steps Run Isolation

By default, steps only consider runs associated with the step parent
when resolving required operations.

We illustrate using the `steps` project.

    >>> project = Project(sample("projects", "steps"))

Here's a typical stepped operation, where required operations are
provided by the parent operation.

    >>> project.run("m6:steps-all")
    INFO: [guild] running upstream: m6:upstream
    INFO: [guild] running downstream: m6:downstream
    Resolving upstream dependency
    Using run ... for upstream resource
    WARNING: nothing resolved for operation:upstream

    >>> project.print_runs(status=True)
    m6:downstream  completed
    m6:upstream    completed
    m6:steps-all   completed

Next we run a broken version - where the downstream operation cannot
resolve an upstream operation because the upstream is not provided by
the step parent.

    >>> project.run("m6:steps-downstream-broken")
    INFO: [guild] running downstream: m6:downstream
    WARNING: cannot find a suitable run for required resource 'upstream'
    Resolving upstream dependency
    guild: run failed because a dependency was not met: could not resolve
    'operation:upstream' in upstream resource: no suitable run for upstream
    <exit 1>

    >>> project.print_runs(status=True)
    m6:downstream               error
    m6:steps-downstream-broken  error
    m6:downstream               completed
    m6:upstream                 completed
    m6:steps-all                completed

This behavior can be modified by setting the step `isolate-runs`
attribute to `no`.

Here's a fixed version, which lets the downstream operation resolve
its upstream requirement from all available runs.

    >>> project.run("m6:steps-downstream-fixed")
    INFO: [guild] running downstream: m6:downstream
    Resolving upstream dependency
    Using run ... for upstream resource
    WARNING: nothing resolved for operation:upstream

    >>> project.print_runs(status=True)
    m6:downstream               completed
    m6:steps-downstream-fixed   completed
    m6:downstream               error
    m6:steps-downstream-broken  error
    m6:downstream               completed
    m6:upstream                 completed
    m6:steps-all                completed

Batch runs do not abide by run isolation as they're run under their
own auspices.

The `steps-batch` operation is an optimizing run that may log warnings
that we're not interested in so we use `LogCapture`.

    >>> with LogCapture():
    ...     project.run("m6:steps-batch")
    INFO: [guild] running loss: m6:loss --max-trials 5 --opt-flag
    random-starts=2 --optimize x='[0:100]'
    INFO: [guild] Random start for optimization (1 of 2)
    INFO: [guild] Running trial ...: m6:loss (x=...)
    loss: ...
    INFO: [guild] Random start for optimization (2 of 2)
    INFO: [guild] Running trial ...: m6:loss (x=...)
    loss: ...
    INFO: [guild] Found 2 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: m6:loss (x=...)
    loss: ...
    INFO: [guild] Found 3 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: m6:loss (x=...)
    loss: ...
    INFO: [guild] Found 4 previous trial(s) for use in optimization
    INFO: [guild] Running trial ...: m6:loss (x=...)
    loss: ...

Note the the batch run is able to find previous trials even through
the trials aren't children of the step parent.
