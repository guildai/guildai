# Dependencies

These are general dependency tests.

    >>> cd(example("dependencies"))

## File

    >>> run("guild run file -y")
    Resolving file:file.txt
    <exit 0>

    >>> run("guild ls -n")
    README.md
    config.json
    config.yml
    file.txt
    guild.yml
    <exit 0>

    >>> run("guild ls -n -s")  # source code
    README.md
    config.json
    config.yml
    guild.yml

    >>> run("guild ls -n -d")  # dependencies
    file.txt

    >>> run("guild ls -n -g")  # generated
    <exit 0>

    >>> run("guild runs info -d")
    id: ...
    flags:
    scalars:
    dependencies:
      file:file.txt:
        file:file.txt:
          paths:
          - .../examples/dependencies/file.txt
          uri: file:file.txt
    <exit 0>

Change dependency source using default source name.

    >>> run("guild run file file:file.txt=file-2.txt -y")
    Resolving file:file.txt
    Using file-2.txt for file:file.txt

`flag-name` is required to explicitly expose file dependency as a
flag.

    >>> run("guild run customizable-file src=file-2.txt -y")
    Resolving src
    Using file-2.txt for src

    >>> run("guild ls -n -d")
    file-2.txt
    <exit 0>

    >>> run("guild runs info -d")
    id: ...
    flags:
      src: file-2.txt
    scalars:
    dependencies:
      src:
        src:
          config: file-2.txt
          paths:
          - .../examples/dependencies/file-2.txt
          uri: file:file.txt
    <exit 0>

Missing file dependency:

    >>> run("guild run missing-file -y")
    Resolving file:missing.txt
    guild: run failed because a dependency was not met: could not resolve
    'file:missing.txt' in file:missing.txt resource: cannot find source
    file 'missing.txt'
    <exit 1>

    >>> run("guild run missing-named-file -y")
    Resolving missing-file
    guild: run failed because a dependency was not met: could not resolve
    'missing-file' in missing-file resource: cannot find source file
    'missing.txt'
    <exit 1>

    >>> run("guild run customizable-file src=missing.txt -y")
    Resolving src
    guild: run failed because a dependency was not met: could not resolve
    'src' in src resource: .../missing.txt does not exist
    <exit 1>

## Directory

    >>> run("guild run dir -y")
    Resolving data
    <exit 0>

    >>> run("guild ls -n -L")
    README.md
    config.json
    config.yml
    dir/
    dir/a
    dir/b
    guild.yml

    >>> run("guild ls -n -s -L")
    README.md
    config.json
    config.yml
    guild.yml

    >>> run("guild ls -n -d -L")
    dir/a
    dir/b

    >>> run("guild ls -n -g -L")
    <exit 0>

    >>> run("guild runs info -d")
    id: ...
    flags:
    scalars:
    dependencies:
      data:
        data:
          paths:
          - .../examples/dependencies/dir
          uri: file:dir
    <exit 0>

## URL

Note that we can't assert the resolution message as the resource may
be cached, which prints a different message.

    >>> run("guild run url -y")
    Resolving https://guild-pub.s3.amazonaws.com/uat/file.txt...
    <exit 0>

    >>> run("guild ls -n")
    README.md
    config.json
    config.yml
    file.txt
    guild.yml
    <exit 0>

    >>> run("guild ls -ns")
    README.md
    config.json
    config.yml
    guild.yml

    >>> run("guild ls -nd")
    file.txt

    >>> run("guild ls -ng")
    <exit 0>

    >>> run("guild runs info -d")
    id: ...
    flags:
    scalars:
    dependencies:
      https://guild-pub.s3.amazonaws.com/uat/file.txt:
        https://guild-pub.s3.amazonaws.com/uat/file.txt:
          paths:
          - .../file.txt
          uri: https://guild-pub.s3.amazonaws.com/uat/file.txt
    <exit 0>

## Operations

Required file op:

    >>> run("guild run file -y")
    Resolving file:file.txt

    >>> run("guild run file-op -y")
    Resolving operation:file
    Using run ... for file operation:file

    >>> run("guild ls -n")
    README.md
    config.json
    config.yml
    file.txt
    guild.yml

    >>> run("guild ls -ns")
    README.md
    config.json
    config.yml
    guild.yml

    >>> run("guild ls -nd")
    file.txt

    >>> run("guild ls -ng")
    <exit 0>

    >>> run("guild runs info -d")
    id: ...
    flags:
      operation:file: ...
    scalars:
    dependencies:
      operation:file:
        operation:file:
          config: ...
          paths:
          - ../.../file.txt
          uri: operation:file
    <exit 0>

Required dir op:

    >>> run("guild run dir-op -y")
    Resolving dir
    Using run ... for operation:dir
    <exit 0>

    >>> run("guild ls -nL")

    >>> run("guild ls -nsL")

    >>> run("guild ls -ndL")

    >>> run("guild ls -ngL")

    >>> run("guild runs info -d")
    id: ...
    flags:
      operation:dir: ...
    scalars:
    dependencies:
      operation:dir:
        operation:dir:
          config: ...
          paths:
          - ../.../dir
          uri: operation:dir
    <exit 0>

## Config

Run without specifying flag values.

    >>> cat(example("dependencies/config.yml"))
    lr: 0.1
    batch-size: 100
    dropout: 0.2

    >>> run("guild run config -y")
    Resolving config:config.yml
    <exit 0>

    >>> run("guild ls -n")
    config.yml
    <exit 0>

    >>> run("guild cat -p config.yml")
    batch-size: 100
    dropout: 0.2
    lr: 0.1
    <exit 0>

    >>> run("guild runs info -d")
    id: ...
    flags:
      batch-size: null
      dropout: null
      lr: null
    scalars:
    dependencies:
      config:config.yml:
        config:config.yml:
          paths:
          - .guild/generated/.../config.yml
          uri: config:config.yml
    <exit 0>

Set two of the three flag values.

    >>> run("guild run config lr=0.2 dropout=0.3 -y")
    Resolving config:config.yml
    <exit 0>

    >>> run("guild ls -n")
    config.yml
    <exit 0>

    >>> run("guild cat -p config.yml")
    batch-size: 100
    dropout: 0.3
    lr: 0.2
    <exit 0>

    >>> run("guild runs info -d")
    id: ...
    flags:
      batch-size: null
      dropout: 0.3
      lr: 0.2
    scalars:
    dependencies:
      config:config.yml:
        config:config.yml:
          paths:
          - .guild/generated/.../config.yml
          uri: config:config.yml
    <exit 0>

Use modified config.

    >>> run("guild run modified-config -y")
    Resolving config:config.yml
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
    Resolving config:config.yml
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
    Resolving config:config.json
    <exit 0>

    >>> run("guild ls -n")
    config.json
    <exit 0>

    >>> run("guild cat -p config.json")
    {"batch-size": 200, "dropout": 0.2, "lr": 0.05}
    <exit 0>

JSON format with flags:

    >>> run("guild run json-config lr=1e-2 -y")
    Resolving config:config.json
    <exit 0>

    >>> run("guild ls -n")
    config.json
    <exit 0>

    >>> run("guild cat -p config.json")
    {"batch-size": 200, "dropout": 0.2, "lr": 0.01}
    <exit 0>

## Modules

    >>> run("guild run modules -y")
    Resolving module:pandas
    Resolving module:sklearn
    <exit 0>

    >>> run("guild runs info -d")
    id: ...
    flags:
    scalars:
    dependencies:
      module:pandas:
        module:pandas:
          paths: []
          uri: module:pandas
      module:sklearn:
        module:sklearn:
          paths: []
          uri: module:sklearn
    <exit 0>

    >>> run("guild run missing-module -y")
    Resolving module:missing.module
    guild: run failed because a dependency was not met: could not
    resolve 'module:missing.module' in module:missing.module resource:
    ...
    <exit 1>

## All Ops

Make sure `all-ops` runs:

    >>> run("guild run all-ops -y")
    INFO: [guild] running file: file
    Resolving file:file.txt
    INFO: [guild] running dir: dir
    Resolving data
    INFO: [guild] running url: url
    Resolving https://guild-pub.s3.amazonaws.com/uat/file.txt
    Using cached file .../file.txt
    INFO: [guild] running file-op: file-op
    Resolving file
    Using run ... for file resource
    INFO: [guild] running dir-op: dir-op
    Resolving dir
    Using run ... for dir resource
    INFO: [guild] running config: config
    Resolving config:config.yml
    INFO: [guild] running modules: modules
    Resolving module:pandas
    Resolving module:sklearn
    INFO: [guild] running downstream: downstream
    Resolving upstream
    Using run ... for upstream resource
    INFO: [guild] running customizable-file: customizable-file src=guild.yml
    Resolving src
    Using guild.yml for src resource
    INFO: [guild] running modified-config: modified-config
    Resolving config:config.yml
    INFO: [guild] running json-config: json-config
    Resolving config:config.json
    <exit 0>

## All resources

`all-resources` resolves a similar set of requirements, configured as
named resources.

    >>> run("guild run all-resources -y") # doctest: +REPORT_UDIFF
    Resolving file
    Resolving dir
    Resolving url
    Using cached file .../file.txt
    Resolving file-op
    Using run ... for file-op resource
    Resolving dir-op
    Using run ... for dir-op resource
    Resolving config
    Resolving modules
    Resolving downstream
    Using run ... for downstream resource
    Resolving customizable-file
    Resolving modified-config
    Resolving json-config
    <exit 0>

    >>> run("guild ls")
    ???:
      config.json
      config.yml
      customizable-file.txt
      dir-op/
      dir-op/a
      dir-op/b
      dir/
      dir/a
      dir/b
      file-file.txt
      file-op.txt
      file.txt
      modified-config.yml
      url-file.txt
    <exit 0>

    >>> run("guild runs info -d")
    id: ...
    flags:
      dir-op: ...
      downstream: ...
      file-op: ...
    scalars:
    dependencies:
      config:
        config:config.yml:
          paths:
          - .guild/generated/.../config.yml
          uri: config:config.yml
      customizable-file:
        file:file.txt:
          paths:
          - .../examples/dependencies/file.txt
          uri: file:file.txt
      dir:
        data:
          paths:
          - .../examples/dependencies/dir
          uri: file:dir
      dir-op:
        operation:dir:
          config: ...
          paths:
          - ../.../dir
          uri: operation:dir
      downstream:
        upstream:
          config: ...
          paths:
          - ../.../file.txt
          uri: operation:file
      file:
        file:file.txt:
          paths:
          - .../examples/dependencies/file.txt
          uri: file:file.txt
      file-op:
        operation:file:
          config: ...
          paths:
          - ../.../file.txt
          uri: operation:file
      json-config:
        config:config.json:
          paths:
          - .guild/generated/.../config.json
          uri: config:config.json
      modified-config:
        config:config.yml:
          paths:
          - .guild/generated/.../config.yml
          uri: config:config.yml
      modules:
        module:pandas:
          paths: []
          uri: module:pandas
        module:sklearn:
          paths: []
          uri: module:sklearn
      url:
        https://guild-pub.s3.amazonaws.com/uat/file.txt:
          paths:
          - .../file.txt
          uri: https://guild-pub.s3.amazonaws.com/uat/file.txt
    <exit 0>
