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
    ...             pprint(dep.inline_resource.data)

## Inline string

An inline string is the traditional way to express a dependency on a
resource.

    >>> gf = guildfile.from_string("""
    ... train:
    ...   requires: prepare
    ... """)

    >>> print_deps(gf.get_operation("train").dependencies)
    <guild.guildfile.OpDependency 'prepare'>
      spec: prepare
      description: ''

A list of strings is treated in the same manner:

    >>> gf = guildfile.from_string("""
    ... train:
    ...   requires:
    ...     - prepare-1
    ...     - prepare-2
    ...     - prepare-3
    ... """)

    >>> print_deps(gf.get_operation("train").dependencies)
    <guild.guildfile.OpDependency 'prepare-1'>
      spec: prepare-1
      description: ''
    <guild.guildfile.OpDependency 'prepare-2'>
      spec: prepare-2
      description: ''
    <guild.guildfile.OpDependency 'prepare-3'>
      spec: prepare-3
      description: ''

## Inline dict - resource spec with description

An inline dict can be either a resource reference or an inline
resource. If the dict contains a `resource` attribute, it's treated as
a resource spec:

    >>> gf = guildfile.from_string("""
    ... train:
    ...   requires:
    ...     resource: data
    ...     description: required data
    ... """)

    >>> print_deps(gf.get_operation("train").dependencies)
    <guild.guildfile.OpDependency 'data'>
      spec: data
      description: required data

## Inline dict - implicit source

If the user provides an inline dict that does not contain a `sources`
attribute, it is treated as an implicit resource source:

    >>> gf = guildfile.from_string("""
    ... train:
    ...   requires:
    ...     url: http://my.co/stuff.gz
    ...     sha256: abc123
    ...     unpack: no
    ... """)

    >>> print_deps(gf.get_operation("train").dependencies)
    <guild.guildfile.OpDependency http://my.co/stuff.gz>
      inline-resource: {'sources': [{'sha256': 'abc123',
                  'unpack': False,
                  'url': 'http://my.co/stuff.gz'}]}

## Inline dict - full resource definition

If the inline dict contains a `sources` attribute, it is treated as a
complete resource definition:

    >>> gf = guildfile.from_string("""
    ... train:
    ...   requires:
    ...     path: data
    ...     sources:
    ...       - url: http://my.co/stuff.gz
    ...         sha256: abc123
    ...         unpack: no
    ...       - url: http://my.co/more-suff.tar
    ...         sha256: dev456
    ... """)

    >>> print_deps(gf.get_operation("train").dependencies)
    <guild.guildfile.OpDependency http://my.co/stuff.gz,http://my.co/more-suff.tar>
      inline-resource: {'path': 'data',
     'sources': [{'sha256': 'abc123',
                  'unpack': False,
                  'url': 'http://my.co/stuff.gz'},
                 {'sha256': 'dev456', 'url': 'http://my.co/more-suff.tar'}]}

## Named inline resources

A resource `name` may be provided for any full resource definition:

    >>> gf = guildfile.from_string("""
    ... train:
    ...   requires:
    ...     name: data
    ...     sources:
    ...       - url: http://my.co/stuff.gz
    ...       - url: http://my.co/more-suff.tar
    ... """)

    >>> print_deps(gf.get_operation("train").dependencies)
    <guild.guildfile.OpDependency data>
      inline-resource: {'name': 'data',
     'sources': [{'url': 'http://my.co/stuff.gz'},
                 {'url': 'http://my.co/more-suff.tar'}]}

## Project tests

The sample project `inline-resources` contains a variety of inline
resource definitions. We can test the resolution of all of the
resources by running the `test-all` operation, which serves as a
validation of the expected results.

    >>> project = Project(sample("projects", "inline-resources"))

    >>> project.run("test-all")
    INFO: [guild] running print-msg: print-msg
    Resolving file:msg.txt dependency
    hola
    INFO: [guild] checking run ... files 'msg.txt'
    INFO: [guild] comparing run ... file msg.txt to .../inline-resources/msg.txt
    INFO: [guild] 1 of 1 checks passed
    INFO: [guild] running print-msg-2: print-msg-2
    Resolving operation:print-msg dependency
    Using output from run ... for operation:print-msg resource
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
