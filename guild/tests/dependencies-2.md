# Dependencies 2

These tests cover the various alternative dependency definition
schemes that were added to simplify dependency definitions.

The primary goal of this simplification is to support inline
dependencies that do not require separate resource definitions.

We'll use a helper to print depepdencies:

    >>> def print_deps(deps):
    ...     for dep in deps:
    ...         print(dep)
    ...         if dep.spec is not None:
    ...             print("  spec: %s" % dep.spec)
    ...         if dep.description is not None:
    ...             print("  description: %s" % (dep.description or "''"))
    ...         if dep.inline_resource:
    ...             print("  inline-resource: ", end="")
    ...             pprint(dep.inline_resource._data)

## Inline string

An inline string is the traditional way to express a dependency on a
resource.

    >>> gf = guildfile.for_string("""
    ... train:
    ...   requires: prepare
    ... """)

    >>> print_deps(gf.default_model["train"].dependencies)
    <guild.guildfile.OpDependencyDef 'prepare'>
      spec: prepare
      description: ''

A list of strings is treated in the same manner:

    >>> gf = guildfile.for_string("""
    ... train:
    ...   requires:
    ...     - prepare-1
    ...     - prepare-2
    ...     - prepare-3
    ... """)

    >>> print_deps(gf.default_model["train"].dependencies)
    <guild.guildfile.OpDependencyDef 'prepare-1'>
      spec: prepare-1
      description: ''
    <guild.guildfile.OpDependencyDef 'prepare-2'>
      spec: prepare-2
      description: ''
    <guild.guildfile.OpDependencyDef 'prepare-3'>
      spec: prepare-3
      description: ''

## Inline dict - resource spec with description

An inline dict can be either a resource reference or an inline
resource. If the dict contains a `resource` attribute, it's treated as
a resource spec:

    >>> gf = guildfile.for_string("""
    ... train:
    ...   requires:
    ...     resource: data
    ...     description: required data
    ... """)

    >>> print_deps(gf.default_model["train"].dependencies)
    <guild.guildfile.OpDependencyDef 'data'>
      spec: data
      description: required data

## Inline dict - implicit source

If the user provides an inline dict that does not contain a `sources`
attribute, it is treated as an implicit resource source:

    >>> gf = guildfile.for_string("""
    ... train:
    ...   requires:
    ...     url: http://my.co/stuff.gz
    ...     sha256: abc123
    ...     unpack: no
    ... """)

    >>> print_deps(gf.default_model["train"].dependencies)
    <guild.guildfile.OpDependencyDef http://my.co/stuff.gz>
      inline-resource: {'sources': [{'sha256': 'abc123',
                  'unpack': False,
                  'url': 'http://my.co/stuff.gz'}]}

## Inline dict - full resource definition

If the inline dict contains a `sources` attribute, it is treated as a
complete resource definition:

    >>> gf = guildfile.for_string("""
    ... train:
    ...   requires:
    ...     target-path: data
    ...     sources:
    ...       - url: http://my.co/stuff.gz
    ...         sha256: abc123
    ...         unpack: no
    ...       - url: http://my.co/more-suff.tar
    ...         sha256: dev456
    ... """)

    >>> print_deps(gf.default_model["train"].dependencies)
    <guild.guildfile.OpDependencyDef http://my.co/stuff.gz,http://my.co/more-suff.tar>
      inline-resource: {'sources': [{'sha256': 'abc123',
                  'unpack': False,
                  'url': 'http://my.co/stuff.gz'},
                 {'sha256': 'dev456', 'url': 'http://my.co/more-suff.tar'}],
     'target-path': 'data'}

## Named inline resources

A resource `name` may be provided for any full resource definition:

    >>> gf = guildfile.for_string("""
    ... train:
    ...   requires:
    ...     name: data
    ...     sources:
    ...       - url: http://my.co/stuff.gz
    ...       - url: http://my.co/more-suff.tar
    ... """)

    >>> print_deps(gf.default_model["train"].dependencies)
    <guild.guildfile.OpDependencyDef data>
      inline-resource: {'name': 'data',
     'sources': [{'url': 'http://my.co/stuff.gz'},
                 {'url': 'http://my.co/more-suff.tar'}]}

## Named and unnamed operation resources

Inline requirements that define an operation but not a name are
implicitly named by their operation.

    >>> gf = guildfile.for_string("""
    ... op1:
    ...   requires:
    ...     - operation: foo
    ... op2:
    ...   requires:
    ...     - operation: foo
    ...       name: FOO
    ... """)

    >>> gf.default_model["op1"].dependencies[0].inline_resource.name
    'foo'

    >>> gf.default_model["op2"].dependencies[0].inline_resource.name
    'FOO'

## Inline list

An inline list can be used to list source. Each list item is converted
to a dependency where `sources` contains a list containing the item.

    >>> gf = guildfile.for_string("""
    ... train:
    ...   requires:
    ...     - url: http://my.co/stuff.gz
    ...     - operation: foo
    ... """)

    >>> print_deps(gf.default_model["train"].dependencies)
    <guild.guildfile.OpDependencyDef http://my.co/stuff.gz>
      inline-resource: {'sources': [{'url': 'http://my.co/stuff.gz'}]}
    <guild.guildfile.OpDependencyDef foo>
      inline-resource: {'sources': [{'operation': 'foo'}]}

## Source paths

As of 0.6.2, a source may contain a path, which is in addition to any
path defined in the source resource. A source path is appended to a
resource path, if a resource path is defined.

    >>> gf = guildfile.for_string("""
    ... train:
    ...   requires:
    ...     - operation: foo
    ...       select: .+\.txt
    ...       target-path: bar
    ... """)

    >>> print_deps(gf.default_model["train"].dependencies) # doctest: -NORMALIZE_PATHS
    <guild.guildfile.OpDependencyDef foo>
      inline-resource: {'sources': [{'operation': 'foo', 'select': '.+\\.txt', 'target-path': 'bar'}]}

    <guild.guildfile.OpDependencyDef foo>
      inline-resource: {'sources': [{'operation': 'foo',
                                     'path': 'bar',
                                     'select': '.+\\.txt'}]}

## Project tests

The sample project `inline-resources` contains a variety of inline
resource definitions. We can test the resolution of all of the
resources by running the `test-all` operation, which serves as a
validation of the expected results.

Note we skip running the operations on Windows because they use POSIX
executables.

    >>> project = Project(sample("projects", "inline-resources"))

Note we skip running the operations on Windows because they use POSIX
executables.

    >>> project.run("test-all") # doctest: -WINDOWS
    INFO: [guild] running print-msg: print-msg
    Resolving file:msg.txt dependency
    hola
    INFO: [guild] checking run ... files 'msg.txt'
    INFO: [guild] comparing run ... file msg.txt to .../inline-resources/msg.txt
    INFO: [guild] 1 of 1 checks passed
    INFO: [guild] running print-msg-2: print-msg-2
    Resolving print-msg dependency
    Using run ... for print-msg resource
    hola
    INFO: [guild] checking run ... files 'msg.txt'
    INFO: [guild] comparing run ... file msg.txt to .../inline-resources/msg.txt
    INFO: [guild] 1 of 1 checks passed
    INFO: [guild] running print-msg-3: print-msg-3
    Resolving file:msg.txt dependency
    Resolving file:msg-2.txt dependency
    hola
    adios
    INFO: [guild] checking run ... files 'msg-1.txt'
    INFO: [guild] comparing run ... file msg-1.txt to .../inline-resources/msg.txt
    INFO: [guild] checking run ... files 'msg-2.txt'
    INFO: [guild] comparing run ... file msg-2.txt to .../inline-resources/msg-2.txt
    INFO: [guild] 2 of 2 checks passed
    INFO: [guild] running print-msg-4: print-msg-4
    Resolving file:msg.txt,file:msg-2.txt dependency
    hola
    adios
    INFO: [guild] checking run ... files 'messages/msg.txt'
    INFO: [guild] comparing run ... file messages/msg.txt to .../inline-resources/msg.txt
    INFO: [guild] checking run ... files 'messages/msg-2.txt'
    INFO: [guild] comparing run ... file messages/msg-2.txt to .../inline-resources/msg-2.txt
    INFO: [guild] 2 of 2 checks passed
