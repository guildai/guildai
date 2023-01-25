# Run Status

    >>> gh = mkdtemp()
    >>> symlink(sample("filter-runs"), path(gh, "runs"))
    >>> set_guild_home(gh)

    >>> run("guild runs")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed   target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed   target=2dc1529b
    [3:2dc1529b]  train      2022-09-01 09:19:33  terminated  noise=0.1 x=1.1
    [4:79ca9e64]  train      2022-09-01 09:19:33  completed   noise=0.1 x=0.1
    [5:ac99cff4]  train      2022-09-01 09:19:33  pending     noise=0.4 x=-1.2
    [6:fe83a924]  train      2022-09-01 09:19:33  error       noise=0.1 x=-1.0
    [7:fa6f74ad]  train      2022-09-01 09:19:33  staged      noise=0.1 x=-1.0

## Completed

    >>> run("guild runs --completed")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed  target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed  target=2dc1529b
    [3:79ca9e64]  train      2022-09-01 09:19:33  completed  noise=0.1 x=0.1

    >>> run("guild runs -Sc")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed  target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed  target=2dc1529b
    [3:79ca9e64]  train      2022-09-01 09:19:33  completed  noise=0.1 x=0.1

    >>> run("guild runs --not-completed")
    [1:2dc1529b]  train  2022-09-01 09:19:33  terminated  noise=0.1 x=1.1
    [2:ac99cff4]  train  2022-09-01 09:19:33  pending     noise=0.4 x=-1.2
    [3:fe83a924]  train  2022-09-01 09:19:33  error       noise=0.1 x=-1.0
    [4:fa6f74ad]  train  2022-09-01 09:19:33  staged      noise=0.1 x=-1.0

## Error

    >>> run("guild runs --error")
    [1:fe83a924]  train  2022-09-01 09:19:33  error  noise=0.1 x=-1.0

    >>> run("guild runs -Se")
    [1:fe83a924]  train  2022-09-01 09:19:33  error  noise=0.1 x=-1.0

    >>> run("guild runs --not-error")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed   target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed   target=2dc1529b
    [3:2dc1529b]  train      2022-09-01 09:19:33  terminated  noise=0.1 x=1.1
    [4:79ca9e64]  train      2022-09-01 09:19:33  completed   noise=0.1 x=0.1
    [5:ac99cff4]  train      2022-09-01 09:19:33  pending     noise=0.4 x=-1.2
    [6:fa6f74ad]  train      2022-09-01 09:19:33  staged      noise=0.1 x=-1.0

## Pending

    >>> run("guild runs --pending")
    [1:ac99cff4]  train  2022-09-01 09:19:33  pending  noise=0.4 x=-1.2

    >>> run("guild runs -Sp")
    [1:ac99cff4]  train  2022-09-01 09:19:33  pending  noise=0.4 x=-1.2

    >>> run("guild runs --not-pending")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed   target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed   target=2dc1529b
    [3:2dc1529b]  train      2022-09-01 09:19:33  terminated  noise=0.1 x=1.1
    [4:79ca9e64]  train      2022-09-01 09:19:33  completed   noise=0.1 x=0.1
    [5:fe83a924]  train      2022-09-01 09:19:33  error       noise=0.1 x=-1.0
    [6:fa6f74ad]  train      2022-09-01 09:19:33  staged      noise=0.1 x=-1.0

## Staged

    >>> run("guild runs --staged")
    [1:fa6f74ad]  train  2022-09-01 09:19:33  staged  noise=0.1 x=-1.0

    >>> run("guild runs -Ss")
    [1:fa6f74ad]  train  2022-09-01 09:19:33  staged  noise=0.1 x=-1.0

    >>> run("guild runs --not-staged")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed   target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed   target=2dc1529b
    [3:2dc1529b]  train      2022-09-01 09:19:33  terminated  noise=0.1 x=1.1
    [4:79ca9e64]  train      2022-09-01 09:19:33  completed   noise=0.1 x=0.1
    [5:ac99cff4]  train      2022-09-01 09:19:33  pending     noise=0.4 x=-1.2
    [6:fe83a924]  train      2022-09-01 09:19:33  error       noise=0.1 x=-1.0

## Error

    >>> run("guild runs --error")
    [1:fe83a924]  train  2022-09-01 09:19:33  error  noise=0.1 x=-1.0

    >>> run("guild runs -Se")
    [1:fe83a924]  train  2022-09-01 09:19:33  error  noise=0.1 x=-1.0

    >>> run("guild runs --not-error")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed   target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed   target=2dc1529b
    [3:2dc1529b]  train      2022-09-01 09:19:33  terminated  noise=0.1 x=1.1
    [4:79ca9e64]  train      2022-09-01 09:19:33  completed   noise=0.1 x=0.1
    [5:ac99cff4]  train      2022-09-01 09:19:33  pending     noise=0.4 x=-1.2
    [6:fa6f74ad]  train      2022-09-01 09:19:33  staged      noise=0.1 x=-1.0

## Multiple

    >>> run("guild runs --completed --error")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed  target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed  target=2dc1529b
    [3:79ca9e64]  train      2022-09-01 09:19:33  completed  noise=0.1 x=0.1
    [4:fe83a924]  train      2022-09-01 09:19:33  error      noise=0.1 x=-1.0

    >>> run("guild runs -Sec")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed  target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed  target=2dc1529b
    [3:79ca9e64]  train      2022-09-01 09:19:33  completed  noise=0.1 x=0.1
    [4:fe83a924]  train      2022-09-01 09:19:33  error      noise=0.1 x=-1.0

    >>> run("guild runs -Ssp")
    [1:ac99cff4]  train  2022-09-01 09:19:33  pending  noise=0.4 x=-1.2
    [2:fa6f74ad]  train  2022-09-01 09:19:33  staged   noise=0.1 x=-1.0

### Special handling for multiple NOT filters

Guild applies an AND operator to status filters when all status
filters are the NOT variant.

    >>> run("guild runs --not-error --not-completed")
    [1:2dc1529b]  train  2022-09-01 09:19:33  terminated  noise=0.1 x=1.1
    [2:ac99cff4]  train  2022-09-01 09:19:33  pending     noise=0.4 x=-1.2
    [3:fa6f74ad]  train  2022-09-01 09:19:33  staged      noise=0.1 x=-1.0

    >>> run("guild runs --not-error --not-completed --not-staged")
    [1:2dc1529b]  train  2022-09-01 09:19:33  terminated  noise=0.1 x=1.1
    [2:ac99cff4]  train  2022-09-01 09:19:33  pending     noise=0.4 x=-1.2

While combining NOT and normal status filters is redundant, or
nonsensical, Guild supports it.

This is supported but `--not-error` is redundant:

    >>> run("guild runs --not-error --staged --completed")
    [1:e394b696]  util:test  2022-09-01 09:33:35  completed  target=fe83a924
    [2:a5520d13]  util:test  2022-09-01 09:33:35  completed  target=2dc1529b
    [3:79ca9e64]  train      2022-09-01 09:19:33  completed  noise=0.1 x=0.1
    [4:fa6f74ad]  train      2022-09-01 09:19:33  staged     noise=0.1 x=-1.0

This command overloads the `error` status with both forms. Guild uses
`--error` form over `--not-error` (the underling implementation using
Click lets this pass through, setting the target argument to
`True`. This is arguably a bug as the expected result should be an
empty list, assuming the two options are applied as specified. This is
an edge case however and would require patching Click or
reimplementing the off switches as separate arguments.)

    >>> run("guild runs --not-error --error")
    [1:fe83a924]  train  2022-09-01 09:19:33  error  noise=0.1 x=-1.0

## Unsupported Status Chars

    >>> run("guild runs -Sxyz")
    guild: unrecognized status char 'x' in option '-S'
    Try 'guild runs --help' for more information.
    <exit 1>
