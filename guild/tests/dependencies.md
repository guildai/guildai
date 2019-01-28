# Dependencies

Guild dependencies are managed by the `deps` module:

    >>> from guild import deps

The primary function of `deps` is to resolve dependencies defined in
operations.

To illustrate, we'll define a model operation that requires a
resource:

    >>> gf = guildfile.from_string("""
    ... - model: sample
    ...   operations:
    ...    test:
    ...      main: <not used>
    ...      requires: data
    ...   resources:
    ...     data:
    ...       sources:
    ...       - abc.txt
    ...       - file: def.txt
    ...       - url: http://foo.com/bar.tar.gz
    ...       - operation: foo/bar:baz
    ... """, "test")

We can get the list of dependencies for an operation with the
`dependencies` attribute:

    >>> test_op = gf.models["sample"].get_operation("test")
    >>> test_op.dependencies
    [<guild.guildfile.OpDependency 'data'>]

The value of `requires` may be a single string or a list of
strings. Each string must be a reference to a model resource. Multiple
values indicate that all resources must be met.

Resource labels may be one of the following types:

- Resource in defined in the operation model
- Resource defined in anothet model in the guildfile
- Resource defined in a model provided by a package

Labels have this grammar:

    [ ( [ PACKAGE '/' ] MODEL ':' ) | ( PACKAGE '/' MODEL ) ] NAME

Where `NAME` is the resource name, `MODEL` is the model the resource
is defined in, and `PACKAGE` is the package containing the model
resource. When referring to a package resource, the model may be
omitted provided there is only one resource with `NAME` provided by
the package.

Here are some examples of dependencies:

| Example           | Dependency                                            |
|-------------------|-------------------------------------------------------|
| data              | resource `data` in the current model                  |
| common:data       | on resource `data` in model `common` in the guildfile |
| mnist/common:data | on `common:data` resource in package `mnist`          |
| mnist/data        | on `data` resource in package `mnist`                 |

Let's look at the required resource:

    >>> data_res = gf.models["sample"].get_resource("data")

This resource has the following sources:

    >>> data_res.sources
    [<guild.resourcedef.ResourceSource 'file:abc.txt'>,
     <guild.resourcedef.ResourceSource 'file:def.txt'>,
     <guild.resourcedef.ResourceSource 'http://foo.com/bar.tar.gz'>,
     <guild.resourcedef.ResourceSource 'operation:foo/bar:baz'>]

## Operation sources

The sample `data` resource above provides a source generated from an
operation. These are known as *operation sources*.

Operation sources must reference a model operation. The operation may
be defined for the source model, another model in the guildfile, or a
model defined in a package. Operation references must be in a format
that can be parsed using `op.OpRef.from_string`.

    >>> from guild.opref import OpRef

`OpRef.from_string` returns a `OpRef` instance if the string can be
parsed as an op ref or raises an exception if it cannot.

Below are various examples.

Operation name only:

    >>> OpRef.from_string("foo")
    OpRef(pkg_type=None,
          pkg_name=None,
          pkg_version=None,
          model_name=None,
          op_name='foo')

Operation of a model in the same guildfile:

    >>> OpRef.from_string("foo:bar")
    OpRef(pkg_type=None,
          pkg_name=None,
          pkg_version=None,
          model_name='foo',
          op_name='bar')

Operation in a packaged model:

    >>> OpRef.from_string("foo/bar:baz")
    OpRef(pkg_type=None,
          pkg_name='foo',
          pkg_version=None,
          model_name='bar',
          op_name='baz')

Some invalid op references:

    >>> OpRef.from_string("")
    Traceback (most recent call last):
    OpRefError: invalid reference: ''

    >>> OpRef.from_string("foo/bar")
    Traceback (most recent call last):
    OpRefError: invalid reference: 'foo/bar'

Here's a helper function to return OpRefs for a give sample run.

    >>> from guild import run as runlib
    >>> def from_run(id):
    ...     path = join_path(sample("opref-runs"), id)
    ...     return runlib.Run(id, path).opref

Below are various examples.

    >>> from_run("guildfile")
    OpRef(pkg_type='guildfile',
          pkg_name='/foo/bar',
          pkg_version='7253deeeaeb6dc85466cf691facff24e',
          model_name='test',
          op_name='go')

    >>> from_run("package")
    OpRef(pkg_type='package',
          pkg_name='fashion',
          pkg_version='1.0',
          model_name='fashion',
          op_name='train')

    >>> from_run("with_space")
    OpRef(pkg_type='guildfile',
          pkg_name='/foo/project with spaces',
          pkg_version='7253deeeaeb6dc85466cf691facff24e',
          model_name='test',
          op_name='go')

    >>> from_run("invalid")
    Traceback (most recent call last):
    OpRefError: invalid opref for run 'invalid'
    (.../samples/opref-runs/invalid): not a valid opref

OpRefs are encoded by converting them to strings.

    >>> str(OpRef("type", "pkg", "ver", "model", "op"))
    'type:pkg ver model op'

If the package name contains a space, it's quoted:

    >>> str(OpRef("type", "pkg with spaces", "ver", "model", "op"))
    "type:'pkg with spaces' ver model op"

OpRefs are compared using their string representations:

    >>> for _ in range(100):
    ...     # If OpRef is using object __cmp__ then this should fail
    ...     # over 100 attempts.
    ...     assert OpRef("", "", "", "", "a") < OpRef("", "", "", "", "b")

## Resolvers

Resolvers are objects that resolve dependency sources. Resolvers can
be obtained for a source via a resource def using the
`get_source_resolver` method.

To illustrate, we'll use a sample project that defines various
resources.

    >>> gf = guildfile.from_dir(sample("projects/resources"))
    >>> res_model = gf.models["resources"]

Here are the model resources:

    >>> res_model.resources
    [<guild.guildfile.ResourceDef 'test'>]

The test resource has the following sources:

    >>> test_resdef = res_model.get_resource("test")
    >>> test_resdef.sources
    [<guild.resourcedef.ResourceSource 'file:archive1.zip'>,
     <guild.resourcedef.ResourceSource 'file:archive2.tar'>,
     <guild.resourcedef.ResourceSource 'file:archive3.tar'>,
     <guild.resourcedef.ResourceSource 'file:test.txt'>,
     <guild.resourcedef.ResourceSource 'file:badhash.txt'>,
     <guild.resourcedef.ResourceSource 'file:files'>,
     <guild.resourcedef.ResourceSource 'file:doesnt-exist'>,
     <guild.resourcedef.ResourceSource 'file:test.txt'>]

In the tests below, we'll use a resolver to resolve each source.

In addition to a source, a resolver needs a resource (see
`guild.deps.Resource`), which is a live representation of the resource
definition. The resource provides additional context to the resolver,
including resource location, the operation that requires the resource,
and additional configuration that may be provided for the resolution
process.

Let's create a resource for our resolvers. The resource requires a
resource def, a location, which is the sample project directory, and a
context.

    >>> test_location = sample("projects/resources")
    >>> test_ctx = deps.ResolutionContext(
    ...   target_dir=None,
    ...   opdef=None,
    ...   resource_config={})

    >>> test_res = deps.Resource(test_resdef, test_location, test_ctx)

### Zip source file

    >>> zip_source = test_resdef.sources[0]
    >>> zip_source.uri
    'file:archive1.zip'

By default, archives are unpacked. See *No unpack archive* below for
an example of an archive that isn't unpacked.

    >>> zip_source.unpack
    True

If a `sha256` hash is specified, the file will be verified before
use. See *Invalid source file* below for an example of a file with an
invalid hash.

    >>> zip_source.sha256
    '8d172fde27ec89ae0a76832f8ff714e3e498b23d14bac7edfb55e3c4729e3265'

    >>> zip_source.select
    ['a.txt']

    >>> resolver = test_resdef.get_source_resolver(zip_source, test_res)
    >>> unpack_dir = mkdtemp()
    >>> log = LogCapture()
    >>> with log:
    ...   resolver.resolve(unpack_dir)
    ['/.../a.txt']

    >>> log.print_all()
    Unpacking .../samples/projects/resources/archive1.zip

    >>> dir(unpack_dir)
    ['.guild-cache-archive1.zip.unpacked', 'a.txt', 'b.txt']

`.guild-cache-FILE.unpacked` is used by Guild to avoid re-scanning the
archive `FILE` for members. For large archives, this saves a lot of
time.

Note that `b.txt` was also extracted into the temp directory. This is
by design - a resource is always fully unpacked when resolved. Files
are selected by way of the source files returned by `resolve`.

### Tar source file

    >>> tar_source = test_resdef.sources[1]
    >>> tar_source.uri
    'file:archive2.tar'

    >>> tar_source.unpack
    True

    >>> print(tar_source.sha256)
    None

    >>> print(tar_source.select)
    []

    >>> resolver = test_resdef.get_source_resolver(tar_source, test_res)
    >>> unpack_dir = mkdtemp()
    >>> log = LogCapture()
    >>> with log:
    ...   sorted(resolver.resolve(unpack_dir))
    ['/.../c.txt', '/.../d.txt']

    >>> log.print_all()
    Unpacking .../samples/projects/resources/archive2.tar

    >>> dir(unpack_dir)
    ['.guild-cache-archive2.tar.unpacked', 'c.txt', 'd.txt']

### No unpack archive

    >>> nounpack_source = test_resdef.sources[2]
    >>> nounpack_source.uri
    'file:archive3.tar'

This source should not be unpacked:

    >>> nounpack_source.unpack
    False

    >>> print(nounpack_source.sha256)
    None

    >>> print(nounpack_source.select)
    []

    >>> resolver = test_resdef.get_source_resolver(nounpack_source, test_res)
    >>> unpack_dir = mkdtemp()
    >>> resolver.resolve(unpack_dir)
    ['.../samples/projects/resources/archive3.tar']

    >>> dir(unpack_dir)
    []

Note the source file is a path directly to the archive and not an
extracted file.

### Plain source file

    >>> plain_source = test_resdef.sources[3]
    >>> plain_source.uri
    'file:test.txt'

    >>> plain_source.sha256
    'f33ae3bc9a22cd7564990a794789954409977013966fb1a8f43c35776b833a95'

    >>> resolver = test_resdef.get_source_resolver(plain_source, test_res)
    >>> unpack_dir = mkdtemp()
    >>> resolver.resolve(unpack_dir)
    ['.../samples/projects/resources/test.txt']

    >>> dir(unpack_dir)
    []

### Invalid source file

    >>> invalid_source = test_resdef.sources[4]
    >>> invalid_source.uri
    'file:badhash.txt'

    >>> invalid_source.sha256
    'xxx'

    >>> resolver = test_resdef.get_source_resolver(invalid_source, test_res)
    >>> unpack_dir = mkdtemp()
    >>> resolver.resolve(unpack_dir)
    Traceback (most recent call last):
    ResolutionError: '.../samples/projects/resources/badhash.txt' has an unexpected
    sha256 (expected xxx but got ...)

    >>> dir(unpack_dir)
    []

### Directory source file

    >>> dir_source = test_resdef.sources[5]
    >>> dir_source.uri
    'file:files'

    >>> resolver = test_resdef.get_source_resolver(dir_source, test_res)
    >>> unpack_dir = mkdtemp()
    >>> sorted(resolver.resolve(unpack_dir))
    ['.../samples/projects/resources/files']

    >>> dir(unpack_dir)
    []

### Non existing source file

    >>> noexist_source = test_resdef.sources[6]
    >>> noexist_source.uri
    'file:doesnt-exist'

    >>> resolver = test_resdef.get_source_resolver(noexist_source, test_res)
    >>> unpack_dir = mkdtemp()
    >>> resolver.resolve(unpack_dir)
    Traceback (most recent call last):
    ResolutionError: cannot find source file doesnt-exist

    >>> dir(unpack_dir)
    []

### Renaming sources

The `rename` attribute can be used to rename resolved sources.

    >>> rename_source = test_resdef.sources[7]
    >>> rename_source.uri
    'file:test.txt'

The rename attr can be a string or a list of strings. Each string
contains two parts, each part separated by a space. If a part contains
spaces it must be quoted.

Here's the rename spec for our source:

    >>> rename_source.rename
    ['(.+)\\.txt \\\\1.config']

Resolve doesn't apply renames - it just resolves the source locations.

    >>> resolver = test_resdef.get_source_resolver(rename_source, test_res)
    >>> unpack_dir = mkdtemp()
    >>> resolver.resolve(unpack_dir)
    ['.../samples/projects/resources/test.txt']

    >>> dir(unpack_dir)
    []

## Resolving sources

NOTE: These tests modify `test_resdef` sources in place. Any tests on
the original source list should be run before these tests.

In these tests we'll resolve some sources to our target
directory. We'll modify `test_resdef` with resolvable sources and
modify `test_ctx` with new target directories so we can see the
resolution results.

### Plain source file

Here's `plain_source` resolved:

    >>> test_resdef.sources = [plain_source]
    >>> test_ctx.target_dir = mkdtemp()
    >>> test_res.resolve()
    ['.../samples/projects/resources/test.txt']

The target directory contains a link to the resolved file.

    >>> dir(test_ctx.target_dir)
    ['test.txt']

    >>> realpath(join_path(test_ctx.target_dir, "test.txt"))
    '.../samples/projects/resources/test.txt'

### Tar source file

Here's the resolved tar source. We'll use a temp directory for
unpacking.

    >>> unpack_dir = mkdtemp("guild-test-unpack-dir-")

And resolve the archive source:

    >>> test_resdef.sources = [tar_source]
    >>> test_ctx.target_dir = mkdtemp()
    >>> with log:
    ...   sorted(test_res.resolve(unpack_dir))
    ['.../guild-test-unpack-dir-.../c.txt',
     '.../guild-test-unpack-dir-.../d.txt']

    >>> log.print_all()
    Unpacking .../samples/projects/resources/archive2.tar

The target directory contains links to unpacked files:

    >>> dir(test_ctx.target_dir)
    ['c.txt', 'd.txt']

    >>> realpath(join_path(test_ctx.target_dir, "c.txt"))
    '.../guild-test-unpack-dir-.../c.txt'

    >>> realpath(join_path(test_ctx.target_dir, "d.txt"))
    '.../guild-test-unpack-dir-.../d.txt'

### No unpack archive

The unpack archive source resolves to the unpacked archive.

    >>> test_resdef.sources = [nounpack_source]
    >>> test_ctx.target_dir = mkdtemp()
    >>> test_res.resolve()
    ['.../samples/projects/resources/archive3.tar']

And the target directory:

    >>> dir(test_ctx.target_dir)
    ['archive3.tar']

    >>> realpath(join_path(test_ctx.target_dir, "archive3.tar"))
    '.../samples/projects/resources/archive3.tar'

### Renamed file

In this test we'll resolve `rename_source`.

    >>> test_resdef.sources = [rename_source]
    >>> test_ctx.target_dir = mkdtemp()
    >>> test_res.resolve()
    ['.../samples/projects/resources/test.txt']

Unlike the previous test, the link is renamed using the source
`rename` spec.

    >>> dir(test_ctx.target_dir)
    ['test.config']

    >>> realpath(join_path(test_ctx.target_dir, "test.config"))
    '.../samples/projects/resources/test.txt'
