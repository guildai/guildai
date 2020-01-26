# Guild Example: `required-operation`

- [guild.yml](guild.yml) - Project Guild file
- [prepare_data.py](prepare_data.py) - Script to simulate preparing a
  data set for training
- [train.py](train.py) - Script to simulate a model build using
  prepared data
- [train2.py](train2.py) - Alternative script for training that
  requires a different data set file layout

This example illustrates how an operation can require the output from
another operation.

## Basics

To run the example, first try to run `train`:

```
$ guild run train
```

`train` requires a run of `prepare-data` and shows a warning message:

```
WARNING: cannot find a suitable run for required resource 'prepared-data'
You are about to run train
  prepared-data: unspecified
Continue? (Y/n) n
```

If you attempt to run the `train` operation, it will fail with an
error message:

```
Resolving prepared-data dependency
guild: run failed because a dependency was not met: could not resolve
'operation:prepare-data' in prepared-data resource: no suitable run for
prepare-data
```

This error indicates that `prepare-data` must be run first.

Run `prepare-data`:

```
$ guild run prepare-data
```

Press `Enter` to start the operation.

`prepare-data` creates some empty files to simulate an actual data
prep operation.

View the prepare-data files:

```
$ guild ls
~/.guild/runs/da39492a99614cbda3ed93500f9623ce:
  data1.txt
  subdir/
  subdir/data2.txt
```

With a `prepare-data` run, we can run train:

```
$ guild run train
```

View the train files:

```
$ guild ls
~/.guild/runs/f31be0c217b749ac8e3709813edd87a0:
  checkpoint.h5
  data/
  data/data1.txt
  data/subdir/
  model.json
```

The mock train files are `model.json` and `checkpoint.h5`. The other
files are links to the files from the `prepare-data` run. Note these
files are located in a `data` subdirectory. This is defined in
[`guild.yml`](guild.yml) using the `path` attribute of the operation
requirement.

You can show the dependencies for a run by including the `-d,
--dependencies` option when running `guild runs info`:

```
$ guild runs info -d
id: f31be0c217b749ac8e3709813edd87a0
<snip>
dependencies:
  prepared-data:
    ~/.guild/runs/da39492a99614cbda3ed93500f9623ce/data1.txt
    ~/.guild/runs/da39492a99614cbda3ed93500f9623ce/subdir
```

The files listed under `dependencies` above show the paths to the
sources used from the prepare-data run.

Next, run `train2`:

```
$ guild run train2
```

List the train2 files:

```
$ guild ls
~/.guild/runs/f7b04e3e26d046ddb824fcea45874a05:
  checkpoint.h5
  data.txt
  model.json
```

Note that `data.txt` is the only file from the `prepare-data`
operation. This is a renamed link to `subdir/data2.txt` from
`prepare-data`. This is controlled defined by the operation
requirement in [`guild.yml`](guild.yml).

Show the dependencies for the train2 run:

```
$ guild runs info -d
id: f7b04e3e26d046ddb824fcea45874a05
...
dependencies:
  prepared-data:
    ~/.guild/runs/da39492a99614cbda3ed93500f9623ce/subdir/data2.txt
```

## Specify a required run

By default Guild uses the latest non-error run for a required
operation. You can specify an alternative run in one of two ways:

- Mark the run you want to use using the `mark` command

- Specify the run ID of the operation you want using flag syntax for
  `prepared-data`

An explicit run ID takes precedence over other methods.

To illustrate, run `prepare-data` a second time to so that there are
multiple `prepare-data` runs:

```
$ guild run prepare-data
```

Confirm you have mutiple prepare-data runs:

```
$ guild runs -o prepare-data
[1:e3afaf34]  prepare-data  2019-07-30 12:58:33  completed
[2:da39492a]  prepare-data  2019-07-30 12:44:00  completed
```

By default, new runs of `train` or `train2` will use the latest run
for `prepare-data` (run `1` in the list). To use an alternative
`prepare-data` run, specify its run ID as follows:

```
$ guild run train prepared-data=da39492a
You are about to run train
  prepared-data: da39492a
Continue? (Y/n)
```

Your run IDs will be different. Replace `da39492a` above with the
applicable `prepare-data` run ID on your system.

If there's a run that you want to use implicitly, use the `mark`
command:

```
$ guild mark da39492a
```

Replace `da39492a` with the applicable run ID on your system.

When you run `train` or `train2` without specifying a value for
`prepared-data` the marked run is used.

```
$ guild run train
```

If you have multiple marked runs, Guild uses the latest marked run of
the required operation. You can clear a mark later using `guild mark
--clear RUN-ID`.
