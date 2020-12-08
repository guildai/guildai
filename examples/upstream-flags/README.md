# Upstream Flags

This example provides a work-around when you want to associate
upstream flag values with a downstream run.

- [guild.yml](guild.yml) - Project Guild file
- [upstream.py](upstream.py) - Sample upstream script
- [downstream.py](downstream.py) - Sample downstream script


The gist:

- Make upstream flags, which is located in upstream runs under
  `.guild/attrs/flags` available to downstream run via operation
  dependency.

- Dynamically modify the downstream runs to include upstream flags,
  which are loaded from the resolved flags YAML file.

First run the upstream operation.

```
$ guild run upstream -y
```

Next run downstream.

```
$ guild run downstream -y
```

List the resolved files for downstream.

```
$ guild ls
upstream-file.txt
upstream-flags.yml
```

These are resolved resources from the upstream dependency.

Show flags for the downstream run.

```
$ guild runs info
id: <downstream run ID>
operation: downstream
...
flags:
  upstream: <upstream run ID>
  upstream-x: 1
  upstream-y: 2
  x: 3
  y: 4
scalars:
```
