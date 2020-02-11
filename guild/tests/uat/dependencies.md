# Dependencies

These are general dependency tests.

    >>> cd(example("dependencies"))

## File

    >>> run("guild run file -y")
    Resolving file:file.txt dependency
    <exit 0>

    >>> run("guild ls -n")
    file.txt
    <exit 0>

Change dependency source using default source name - not allowed.

    >>> run("guild run file file:file.txt=guild.yml -y")
    guild: unsupported flag 'file:file.txt'
    Try 'guild run file --help-op' for a list of flags or use
    --force-flags to skip this check.
    <exit 1>

`flag-name` is required to explicitly expose file dependency as a
flag.

    >>> run("guild run customizable-file src=guild.yml -y")
    Resolving src dependency
    Using guild.yml for src resource
    <exit 0>

    >>> run("guild ls -n")
    guild.yml
    <exit 0>

Missing file dependency:

    >>> run("guild run missing-file -y")
    Resolving file:missing.txt dependency
    guild: run failed because a dependency was not met: could not resolve
    'file:missing.txt' in file:missing.txt resource: cannot find source
    file missing.txt
    <exit 1>

    >>> run("guild run missing-named-file -y")
    Resolving missing-file dependency
    guild: run failed because a dependency was not met: could not resolve
    'file:missing.txt' in missing-file resource: cannot find source file
    missing.txt
    <exit 1>

    >>> run("guild run customizable-file src=missing.txt -y")
    Resolving src dependency
    guild: run failed because a dependency was not met: could not resolve
    'file:file.txt' in src resource: .../missing.txt does not exist
    <exit 1>

## Directory

    >>> run("guild run dir -y")
    Resolving data dependency
    <exit 0>

    >>> run("guild ls -n -L")
    dir/
    dir/a
    dir/b
    <exit 0>

## URL

Note that we can't assert the resolution message as the resource may
be cached, which prints a different message.

    >>> run("guild run url -y")
    Resolving https://guild-pub.s3.amazonaws.com/uat/file.txt dependency
    ...
    <exit 0>

    >>> run("guild ls -n")
    file.txt
    <exit 0>

## Operations

Required file op:

    >>> run("guild run file-op -y")
    Resolving file dependency
    Using output from run ... for file resource
    <exit 0>

    >>> run("guild ls -n")
    file.txt
    <exit 0>

Required dir op:

    >>> run("guild run dir-op -y")
    Resolving dir dependency
    Using output from run ... for dir resource
    <exit 0>

    >>> run("guild ls -nL")
    dir/
    dir/a
    dir/b
    <exit 0>

## Config

Run without specifying flag values.

    >>> cat(example("dependencies/config.yml"))
    lr: 0.1
    batch-size: 100
    dropout: 0.2

    >>> run("guild run config -y")
    Resolving config:config.yml dependency
    <exit 0>

    >>> run("guild ls -n")
    config.yml
    <exit 0>

    >>> run("guild cat -p config.yml")
    batch-size: 100
    dropout: 0.2
    lr: 0.1
    <exit 0>

Set two of the three flag values.

    >>> run("guild run config lr=0.2 dropout=0.3 -y")
    Resolving config:config.yml dependency
    <exit 0>

    >>> run("guild ls -n")
    config.yml
    <exit 0>

    >>> run("guild cat -p config.yml")
    batch-size: 100
    dropout: 0.3
    lr: 0.2
    <exit 0>

Use modified config.

    >>> run("guild run modified-config -y")
    Resolving config:config.yml dependency
    <exit 0>

    >>> run("guild ls -n")
    config.yml
    <exit 0>

    >>> run("guild cat -p config.yml")
    batch-size: 100
    dropout: 0.4
    lr: 0.001
    <exit 0>

Change modified config with flags:

    >>> run("guild run modified-config dropout=0.5 -y")
    Resolving config:config.yml dependency
    <exit 0>

    >>> run("guild ls -n")
    config.yml
    <exit 0>

    >>> run("guild cat -p config.yml")
    batch-size: 100
    dropout: 0.5
    lr: 0.001
    <exit 0>

JSON format:

    >>> cat(example("dependencies/config.json"))
    {
      "lr": 0.05,
      "batch-size": 200,
      "dropout": 0.2
    }

    >>> run("guild run json-config -y")
    Resolving config:config.json dependency
    <exit 0>

    >>> run("guild ls -n")
    config.json
    <exit 0>

    >>> run("guild cat -p config.json")
    {"batch-size": 200, "dropout": 0.2, "lr": 0.05}
    <exit 0>

JSON format with flags:

    >>> run("guild run json-config lr=1e-2 -y")
    Resolving config:config.json dependency
    <exit 0>

    >>> run("guild ls -n")
    config.json
    <exit 0>

    >>> run("guild cat -p config.json")
    {"batch-size": 200, "dropout": 0.2, "lr": 0.01}
    <exit 0>

## Modules

    >>> run("guild run modules -y")
    Resolving module:pandas dependency
    Resolving module:sklearn dependency
    <exit 0>

    >>> run("guild run missing-module -y")
    Resolving module:missing.module dependency
    guild: run failed because a dependency was not met: could not
    resolve 'module:missing.module' in module:missing.module resource:
    ...
    <exit 1>

## All

    >>> run("guild run all -y", ignore="Refreshing") # doctest: +REPORT_UDIFF
    INFO: [guild] running file: file
    Resolving file:file.txt dependency
    INFO: [guild] running dir: dir
    Resolving data dependency
    INFO: [guild] running url: url
    Resolving https://guild-pub.s3.amazonaws.com/uat/file.txt dependency
    ...
    INFO: [guild] running file-op: file-op
    Resolving file dependency
    Using output from run ... for file resource
    INFO: [guild] running dir-op: dir-op
    Resolving dir dependency
    Using output from run ... for dir resource
    INFO: [guild] running config: config
    Resolving config:config.yml dependency
    INFO: [guild] running modules: modules
    Resolving module:pandas dependency
    Resolving module:sklearn dependency
    INFO: [guild] running downstream: downstream
    Resolving upstream dependency
    Using output from run ... for upstream resource
    INFO: [guild] running customizable-file: customizable-file src=guild.yml
    Resolving src dependency
    Using guild.yml for src resource
    INFO: [guild] running modified-config: modified-config
    Resolving config:config.yml dependency
    INFO: [guild] running json-config: json-config
    Resolving config:config.json dependency
    <exit 0>
