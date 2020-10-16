# Dependencies

Guild dependencies are managed by the `op_dep` module:

    >>> from guild import op_dep

The primary function of `op_dep` is to resolve dependencies defined in
operations.

To illustrate, we'll define a model operation that requires a
resource:

    >>> gf = guildfile.for_string("""
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

    >>> test_op = gf.models["sample"]["test"]
    >>> test_op.dependencies
    [<guild.guildfile.OpDependencyDef 'data'>]

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
that can be parsed using `op.OpRef.for_string`.

    >>> from guild.opref import OpRef

`OpRef.for_string` returns a `OpRef` instance if the string can be
parsed as an op ref or raises an exception if it cannot.

Below are various examples.

Operation name only:

    >>> OpRef.for_string("foo")
    OpRef(pkg_type=None,
          pkg_name=None,
          pkg_version=None,
          model_name=None,
          op_name='foo')

Operation of a model in the same guildfile:

    >>> OpRef.for_string("foo:bar")
    OpRef(pkg_type=None,
          pkg_name=None,
          pkg_version=None,
          model_name='foo',
          op_name='bar')

Operation in a packaged model:

    >>> OpRef.for_string("foo/bar:baz")
    OpRef(pkg_type=None,
          pkg_name='foo',
          pkg_version=None,
          model_name='bar',
          op_name='baz')

Some invalid op references:

    >>> OpRef.for_string("")
    Traceback (most recent call last):
    OpRefError: invalid reference: ''

    >>> OpRef.for_string("foo/bar")
    Traceback (most recent call last):
    OpRefError: invalid reference: 'foo/bar'

Here's a helper function to return OpRefs for a give sample run.

    >>> from guild import run as runlib
    >>> def for_run(id):
    ...     path = join_path(sample("opref-runs"), id)
    ...     return runlib.Run(id, path).opref

Helper to create resolve contexts:

    >>> import guild.resolver
    >>> def ResolveContext(run=None):
    ...     return guild.resolver.ResolveContext(
    ...         unpack_dir=mkdtemp("guild-test-unpack-dir-"),
    ...         run=run
    ...     )

Below are various examples.

    >>> for_run("guildfile")
    OpRef(pkg_type='guildfile',
          pkg_name='/foo/bar',
          pkg_version='7253deeeaeb6dc85466cf691facff24e',
          model_name='test',
          op_name='go')

    >>> for_run("package")
    OpRef(pkg_type='package',
          pkg_name='fashion',
          pkg_version='1.0',
          model_name='fashion',
          op_name='train')

    >>> for_run("with_space")
    OpRef(pkg_type='guildfile',
          pkg_name='/foo/project with spaces',
          pkg_version='7253deeeaeb6dc85466cf691facff24e',
          model_name='test',
          op_name='go')

    >>> for_run("invalid")
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
be obtained for a source via a resource def using
`guild.resolver.for_resdef_source`.

    >>> from guild.resolver import for_resdef_source as get_resolver

To illustrate, we'll use a sample project that defines various
resources.

    >>> gf = guildfile.for_dir(sample("projects", "resources"))
    >>> res_model = gf.models["resources"]

Here are the model resources:

    >>> res_model.resources
    [<guild.guildfile.ResourceDef 'test'>,
     <guild.guildfile.ResourceDef 'test2'>,
     <guild.guildfile.ResourceDef 'test3'>,
     <guild.guildfile.ResourceDef 'test4'>,
     <guild.guildfile.ResourceDef 'test5'>,
     <guild.guildfile.ResourceDef 'test6'>]

### test resource

The test resource has the following sources:

    >>> test_resdef = res_model.get_resource("test")
    >>> test_resdef.sources
    [<guild.resourcedef.ResourceSource 'file:archive1.zip'>,
     <guild.resourcedef.ResourceSource 'file:archive2.tar'>,
     <guild.resourcedef.ResourceSource 'file:archive3.tar'>,
     <guild.resourcedef.ResourceSource 'file:test.txt'>,
     <guild.resourcedef.ResourceSource 'file:badhash.txt'>,
     <guild.resourcedef.ResourceSource 'file:files'>,
     <guild.resourcedef.ResourceSource 'file:files'>,
     <guild.resourcedef.ResourceSource 'file:doesnt-exist'>,
     <guild.resourcedef.ResourceSource 'file:test.txt'>,
     <guild.resourcedef.ResourceSource 'file:foo'>,
     <guild.resourcedef.ResourceSource 'file:foo.zip'>,
     <guild.resourcedef.ResourceSource 'file:foo.zip'>,
     <guild.resourcedef.ResourceSource 'file:foo'>,
     <guild.resourcedef.ResourceSource 'file:foo'>,
     <guild.resourcedef.ResourceSource 'file:foo'>]

In the tests below, we'll use a resolver to resolve each source.

Helper to resolve a source:

    >>> def resolve(source, context_run=None):
    ...     context_run = context_run or runlib.for_dir(mkdtemp())
    ...     #target_dir = context_run.dir if context_run else mkdtemp()
    ...     #ctx = deps.ResolutionContext(
    ...     #    target_dir=target_dir,
    ...     #    opdef=None,
    ...     #    resource_config={})
    ...     project_dir = sample("projects", "resources")
    ...     #res = deps.Resource(source.resdef, project_dir, ctx)
    ...     dep = op_dep.OpDependency(source.resdef, project_dir, {})
    ...     resolve_context = ResolveContext(context_run)
    ...     resolved = op_dep.resolve_source(source, dep, resolve_context)
    ...     #resolved = res.resolve_source(source, resolve_context)
    ...     for i, val in enumerate(resolved):
    ...         resolved[i] = val.replace(resolve_context.unpack_dir, "<unpack-dir>") \
    ...                          .replace(project_dir, "<project-dir>")
    ...         if context_run:
    ...             resolved[i] = resolved[i].replace(context_run.dir, "<run-dir>")
    ...     staged = findl(context_run.dir)
    ...     unpacked = findl(resolve_context.unpack_dir)
    ...     pprint({"resolved": resolved, "staged": staged, "unpacked": unpacked})

#### Zip source file

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
    [SelectSpec(pattern='a.txt', reduce=None)]

    >>> with LogCapture() as log:
    ...     resolve(zip_source)
    {'resolved': ['<unpack-dir>/a.txt'],
     'staged': ['a.txt'],
     'unpacked': ['.guild-cache-archive1.zip.unpacked', 'a.txt', 'b.txt']}

    >>> log.print_all()
    Unpacking .../samples/projects/resources/archive1.zip

`.guild-cache-<filename>.unpacked` is used by Guild to avoid
re-scanning the archive `FILE` for members. For large archives, this
saves a lot of time.

Note that `b.txt` is also unpacked. This is by design - a resource is
always fully unpacked when resolved. Resolved files are selected from
the unpacked location..

#### Tar source file

The source in this example unpacks and selects all of the files in
`archive2.tar`.

    >>> tar_source = test_resdef.sources[1]
    >>> tar_source.uri
    'file:archive2.tar'

By default, archives are unpacked.

    >>> tar_source.unpack
    True

    >>> print(tar_source.sha256)
    None

An empty select spec implies 'select everything'.

    >>> print(tar_source.select)
    []

    >>> with LogCapture() as log:
    ...     resolve(tar_source)
    {'resolved': ['<unpack-dir>/a.txt', '<unpack-dir>/b.txt', '<unpack-dir>/ccc'],
     'staged': ['a.txt', 'b.txt', 'ccc'],
     'unpacked': ['.guild-cache-archive2.tar.unpacked',
                  'a.txt',
                  'b.txt',
                  'ccc/c.txt',
                  'ccc/ddd/d.txt']}

    >>> log.print_all()
    Unpacking .../samples/projects/resources/archive2.tar

#### No unpack archive

The source in this example is like the previous source but specifies
`unpack` as false to ensure that the file is resolved as-is without
unpacking. `unpack` is only needed for known archives.

    >>> nounpack_source = test_resdef.sources[2]
    >>> nounpack_source.uri
    'file:archive3.tar'

`unpack` is False.

    >>> nounpack_source.unpack
    False

    >>> print(nounpack_source.sha256)
    None

    >>> print(nounpack_source.select)
    []

    >>> resolve(nounpack_source)
    {'resolved': ['<project-dir>/archive3.tar'],
     'staged': ['archive3.tar'],
     'unpacked': []}

Note the source file is a path directly to the archive and not an
extracted file.

#### Plain source file

In this example, the source is a text file that can be checked using a
sha.

    >>> plain_source = test_resdef.sources[3]
    >>> plain_source.uri
    'file:test.txt'

    >>> plain_source.sha256
    'f33ae3bc9a22cd7564990a794789954409977013966fb1a8f43c35776b833a95'

    >>> resolve(plain_source)
    {'resolved': ['<project-dir>/test.txt'],
     'staged': ['test.txt'],
     'unpacked': []}

#### Invalid source file

This example illustrates a resolution failure because a sha doesn't
match.

    >>> invalid_source = test_resdef.sources[4]
    >>> invalid_source.uri
    'file:badhash.txt'

    >>> invalid_source.sha256
    'xxx'

    >>> resolve(invalid_source)
    Traceback (most recent call last):
    OpDependencyError: could not resolve 'file:badhash.txt' in test resource:
    '.../samples/projects/resources/badhash.txt' has an unexpected sha256
    (expected xxx but got ...)


#### Directory source file

When a file is a directory and it doesn't specify a `select`
attribute, just the directory path is resolved:

    >>> dir_source = test_resdef.sources[5]
    >>> dir_source.uri
    'file:files'

    >>> dir_source.select
    []

    >>> resolve(dir_source)
    {'resolved': ['<project-dir>/files'], 'staged': ['files'], 'unpacked': []}

When a file is a directory and specifies a `select`, files that are
selected from the directory are resolved:

    >>> dir_source_2 = test_resdef.sources[6]
    >>> dir_source_2.uri
    'file:files'

    >>> dir_source_2.select # doctest: -NORMALIZE_PATHS
    [SelectSpec(pattern='.+\\.txt', reduce=None)]

    >>> resolve(dir_source_2)
    {'resolved': ['<project-dir>/files/e.txt', '<project-dir>/files/f.txt'],
     'staged': ['e.txt', 'f.txt'],
     'unpacked': []}

#### Non existing source file

Non-existing files generate an error when resolved:

    >>> noexist_source = test_resdef.sources[7]
    >>> noexist_source.uri
    'file:doesnt-exist'

    >>> resolve(noexist_source)
    Traceback (most recent call last):
    OpDependencyError: could not resolve 'file:doesnt-exist' in test resource:
    cannot find source file 'doesnt-exist'

#### Renaming sources

The `rename` attribute can be used to rename resolved sources.

    >>> rename_source = test_resdef.sources[8]
    >>> rename_source.uri
    'file:test.txt'

The rename attr can be a string or a list of strings. Each string
contains two parts, each part separated by a space. If a part contains
spaces it must be quoted.

Here's the rename spec for our source:

    >>> rename_source.rename # doctest: -NORMALIZE_PATHS
    [RenameSpec(pattern='(.+)\\.txt', repl='\\1.config')]

    >>> resolve(rename_source)
    {'resolved': ['<project-dir>/test.txt'],
     'staged': ['test.config'],
     'unpacked': []}

#### Selecting from dirs

If a directory is specified using a `file` source, the `select`
attribute can specify paths within that directory to link to.

    >>> dir_source_2 = test_resdef.sources[9]
    >>> dir_source_2.uri
    'file:foo'

    >>> dir_source_2.select
    [SelectSpec(pattern='bar', reduce=None),
     SelectSpec(pattern='a.txt', reduce=None)]

    >>> resolve(dir_source_2)
    {'resolved': ['<project-dir>/foo/a.txt', '<project-dir>/foo/bar'],
     'staged': ['a.txt', 'bar'],
     'unpacked': []}

#### Selecting from archive

This example shows selecting a directory (really a prefix within the
archive) from an archive.

    >>> zip_source_2 = test_resdef.sources[10]
    >>> zip_source_2.uri
    'file:foo.zip'

    >>> zip_source_2.select
    [SelectSpec(pattern='foo/bar', reduce=None),
     SelectSpec(pattern='foo/a.txt', reduce=None)]

The pattern `foo/bar` specifies that the unpacked directory should be
resolved.

    >>> with LogCapture() as log:
    ...     resolve(zip_source_2)
    {'resolved': ['<unpack-dir>/foo/a.txt', '<unpack-dir>/foo/bar'],
     'staged': ['a.txt', 'bar'],
     'unpacked': ['.guild-cache-foo.zip.unpacked',
                  'foo/a.txt',
                  'foo/bar/a.txt',
                  'foo/bar/b.txt']}

    >>> log.print_all()
    Unpacking .../samples/projects/resources/foo.zip

In this example, the same archive is used to select `*.txt` files
from.

    >>> zip_source_3 = test_resdef.sources[11]
    >>> zip_source_3.uri
    'file:foo.zip'

    >>> zip_source_3.select  # doctest: -NORMALIZE_PATHS
    [SelectSpec(pattern='.+\\.txt', reduce=None)]

    >>> with LogCapture() as log:
    ...     resolve(zip_source_3)
    {'resolved': ['<unpack-dir>/foo/a.txt',
                  '<unpack-dir>/foo/bar/a.txt',
                  '<unpack-dir>/foo/bar/b.txt'],
     'staged': ['a.txt', 'b.txt'],
     'unpacked': ['.guild-cache-foo.zip.unpacked',
                  'foo/a.txt',
                  'foo/bar/a.txt',
                  'foo/bar/b.txt']}

    >>> log.print_all()
    Unpacking .../samples/projects/resources/foo.zip
    WARNING: .../a.txt already exists, skipping link

There is more than one file that matches `a.txt` so Guild prints a
warnings message that it skipped creating the second link.

### Nothing selected

Sources 12, 13, and 14 demonstrate behavior when nothing is selected.

Default behavior is to warn if nothing is resolved:

    >>> nothing_selected_default = test_resdef.sources[12]
    >>> nothing_selected_default.uri
    'file:foo'

    >>> nothing_selected_default.warn_if_empty
    True

    >>> nothing_selected_default.fail_if_empty
    False

    >>> with LogCapture() as log:
    ...     resolve(nothing_selected_default)
    {'resolved': [], 'staged': [], 'unpacked': []}

    >>> log.print_all()
    WARNING: nothing resolved for file:foo

Warning can be disabled with `warn-if-empty: false`:

    >>> nothing_selected_warn = test_resdef.sources[13]
    >>> nothing_selected_warn.uri
    'file:foo'

    >>> nothing_selected_warn.warn_if_empty
    False

    >>> nothing_selected_warn.fail_if_empty
    False

    >>> with LogCapture() as log:
    ...     resolve(nothing_selected_warn)
    {'resolved': [], 'staged': [], 'unpacked': []}

    >>> log.print_all()

A resolution can be made to fail by setting `fail-if-empty` to `true`:

    >>> nothing_selected_fail = test_resdef.sources[14]
    >>> nothing_selected_fail.uri
    'file:foo'

    >>> nothing_selected_fail.warn_if_empty
    True

    >>> nothing_selected_fail.fail_if_empty
    True

    >>> resolve(nothing_selected_fail)
    Traceback (most recent call last):
    OpDependencyError: could not resolve 'file:foo' in test resource: nothing
    resolved for file:foo

### test2 resource

The `test2` resource uses paths to save resolved sources under a
directory.

    >>> test2_resdef = res_model.get_resource("test2")
    >>> test2_resdef.sources
    [<guild.resourcedef.ResourceSource 'file:test.txt'>,
     <guild.resourcedef.ResourceSource 'file:files/a.bin'>,
     <guild.resourcedef.ResourceSource 'file:test.txt'>]

The default path is defined at the resource level:

    >>> test2_resdef.target_path
    'foo'

#### Resource-level target path

The first source doesn't specify a path and therefore uses the
resource path.

    >>> file_nopath = test2_resdef.sources[0]
    >>> file_nopath.uri
    'file:test.txt'

    >>> print(file_nopath.target_path)
    None

    >>> resolve(file_nopath)
    {'resolved': ['<project-dir>/test.txt'],
     'staged': ['foo/test.txt'],
     'unpacked': []}

#### Source-level target path

The second resource does specify a path. This path replaces the
resource path.

    >>> file_path = test2_resdef.sources[1]
    >>> file_path.uri
    'file:files/a.bin'

    >>> file_path.target_path
    'bar'

    >>> file_path.resdef.target_path
    'foo'

    >>> resolve(file_path)
    {'resolved': ['<project-dir>/files/a.bin'],
     'staged': ['bar/a.bin'],
     'unpacked': []}

#### Absolute target path

A target path cannot be absolute.

    >>> abs_path = test2_resdef.sources[2]

    >>> abs_path.target_path
    '/abs/path'

    >>> resolve(abs_path)
    Traceback (most recent call last):
    OpDependencyError: invalid path '/abs/path' in test2 resource (path must be relative)

### test3 resource

The `test3` resource contains a more complex rename spec.

    >>> test3_resdef = res_model.get_resource("test3")
    >>> test3_resdef.sources
    [<guild.resourcedef.ResourceSource 'file:files'>,
     <guild.resourcedef.ResourceSource 'file:files'>,
     <guild.resourcedef.ResourceSource 'file:archive1.zip'>,
     <guild.resourcedef.ResourceSource 'file:archive2.tar'>]

#### Renamed directory

The first source specifies the `files` directory but renames it to
`all_files`.

    >>> all_files = test3_resdef.sources[0]
    >>> all_files.uri
    'file:files'

    >>> print(all_files.target_path)
    None

    >>> all_files.select
    []

    >>> all_files.rename
    [RenameSpec(pattern='files', repl='all_files')]

    >>> resolve(all_files)
    {'resolved': ['<project-dir>/files'], 'staged': ['all_files'], 'unpacked': []}

#### bin files

The second source selects *.bin files from `files` and renames them to
strip off the `.bin` suffix. The files are additionally stored in a
`bin` directory (path).

    >>> bin_files = test3_resdef.sources[1]
    >>> bin_files.uri
    'file:files'

    >>> bin_files.target_path
    'bin'

    >>> bin_files.select # doctest: -NORMALIZE_PATHS
    [SelectSpec(pattern='.+\\.bin', reduce=None)]

    >>> bin_files.rename
    [RenameSpec(pattern='.bin', repl='')]

    >>> resolve(bin_files)
    {'resolved': ['<project-dir>/files/a.bin'],
     'staged': ['bin/a'],
     'unpacked': []}

#### archive1 text files

The third source selects text files from `archive1.zip`, stores them
in an `archive1` directory (path) and adds a `2` to their basename.

    >>> archive1_txt_files = test3_resdef.sources[2]
    >>> archive1_txt_files.uri
    'file:archive1.zip'

    >>> archive1_txt_files.target_path
    'archive1'

    >>> archive1_txt_files.select # doctest: -NORMALIZE_PATHS
    [SelectSpec(pattern='.+\\.txt', reduce=None)]

    >>> archive1_txt_files.rename # doctest: -NORMALIZE_PATHS
    [RenameSpec(pattern='(.+)\\.txt', repl='\\g<1>2.txt')]

    >>> with LogCapture() as log:
    ...     resolve(archive1_txt_files)
    {'resolved': ['<unpack-dir>/a.txt', '<unpack-dir>/b.txt'],
     'staged': ['archive1/a2.txt', 'archive1/b2.txt'],
     'unpacked': ['.guild-cache-archive1.zip.unpacked', 'a.txt', 'b.txt']}

    >>> log.print_all()
    Unpacking .../samples/projects/resources/archive1.zip

#### All archive2 files

The fourth source selects all of the files from `archive2.tar` and
renames them with an `archive2_` prefix.

    >>> archive2_files = test3_resdef.sources[3]
    >>> archive2_files.uri
    'file:archive2.tar'

    >>> print(archive2_files.target_path)
    None

    >>> archive2_files.select
    []

    >>> archive2_files.rename # doctest: -NORMALIZE_PATHS
    [RenameSpec(pattern='(.+)', repl='archive2_\\1')]

    >>> with LogCapture() as log:
    ...     resolve(archive2_files)
    {'resolved': ['<unpack-dir>/a.txt', '<unpack-dir>/b.txt', '<unpack-dir>/ccc'],
     'staged': ['archive2_a.txt', 'archive2_b.txt', 'archive2_ccc'],
     'unpacked': ['.guild-cache-archive2.tar.unpacked',
                  'a.txt',
                  'b.txt',
                  'ccc/c.txt',
                  'ccc/ddd/d.txt']}

    >>> log.print_all()
    Unpacking .../samples/projects/resources/archive2.tar

### test4 resource

The test4 resource contains config sources.

    >>> test4_resdef = res_model.get_resource("test4")
    >>> test4_resdef.sources
    [<guild.resourcedef.ResourceSource 'config:config.yml'>,
     <guild.resourcedef.ResourceSource 'config:config.yml'>,
     <guild.resourcedef.ResourceSource 'config:config.yml'>]

#### Simple config

The first config source simply resolves the source file as is.

    >>> simple_config = test4_resdef.sources[0]
    >>> simple_config.uri
    'config:config.yml'

Config resolves require a run, which is used for storing generated
files and for reading run flags.

    >>> run = runlib.for_dir(mkdtemp())
    >>> run.init_skel()

    >>> resolve(simple_config, run)
    {'resolved': ['<run-dir>/.guild/generated/.../config.yml'],
     'staged': ['.guild/attrs/id',
                '.guild/attrs/initialized',
                '.guild/generated/.../config.yml',
                'config.yml'],
     'unpacked': []}

And the config:

    >>> cat(join_path(run.dir, "config.yml"))
    a: 1
    b: 2
    c:
      d: 3

Here the config is the same as the source:

    >>> cat(sample("projects", "resources", "config.yml"))
    a: 1
    b: 2
    c:
      d: 3

#### Renamed config with flags

The second config is renamed:

    >>> renamed_config = test4_resdef.sources[1]
    >>> renamed_config.uri
    'config:config.yml'

    >>> renamed_config.rename
    [RenameSpec(pattern='config', repl='c2')]

When we resolve this source, we'll apply flag values. Flag values are
defined by the context run. Let's create one with some flag vals:

    >>> run = runlib.for_dir(mkdtemp())
    >>> run.init_skel()
    >>> run.write_attr("flags", {"a": 11, "b": "22", "c.d": 33})

    >>> resolve(renamed_config, run)
    {'resolved': ['<run-dir>/.guild/generated/.../config.yml'],
     'staged': ['.guild/attrs/flags',
                '.guild/attrs/id',
                '.guild/attrs/initialized',
                '.guild/generated/.../config.yml',
                'c2.yml'],
     'unpacked': []}

Here's the resolved and renamed config file:

    >>> cat(join_path(run.dir, "c2.yml"))
    a: 11
    b: '22'
    c:
      d: 33

Note that the flag values are applied to each of the applicable config
values using the "nested flags" syntax, which uses dots to delimit
config levels (see flag names above).

#### Config with params

Out third source defines params that are applied to config.

    >>> param_config = test4_resdef.sources[2]
    >>> param_config.uri
    'config:config.yml'

    >>> pprint(param_config.params)
    {'a': 111, 'c.d': 333}

This source is also stored under a path:

    >>> param_config.target_path
    'c3'

Resolve in the context of a run without flags:

    >>> run = runlib.for_dir(mkdtemp())
    >>> run.init_skel()

    >>> resolve(param_config, run)
    {'resolved': ['<run-dir>/.guild/generated/.../config.yml'],
     'staged': ['.guild/attrs/id',
                '.guild/attrs/initialized',
                '.guild/generated/.../config.yml',
                'c3/config.yml'],
     'unpacked': []}

The resolved config under a path:

    >>> cat(join_path(run.dir, "c3/config.yml"))
    a: 111
    b: 2
    c:
      d: 333

Note the new values for `a` and `c.d` -- these values are provided by
the params (see above).

Let's resolve with a run that has flags.

    >>> run = runlib.for_dir(mkdtemp())
    >>> run.init_skel()
    >>> run.write_attr("flags", {"b": 222, "c.d": 444, "e": "hello"})

    >>> resolve(param_config, run)
    {'resolved': ['<run-dir>/.guild/generated/.../config.yml'],
     'staged': ['.guild/attrs/flags',
                '.guild/attrs/id',
                '.guild/attrs/initialized',
                '.guild/generated/.../config.yml',
                'c3/config.yml'],
     'unpacked': []}

    >>> cat(join_path(run.dir, "c3/config.yml"))
    a: 111
    b: 222
    c:
      d: 444
    e: hello

### test5 resources

The `test5` resource illustrates different `target-type` attributes.

    >>> test5_resdef = res_model.get_resource("test5")
    >>> test5_resdef.sources
    [<guild.resourcedef.ResourceSource 'default-type'>,
     <guild.resourcedef.ResourceSource 'copy-type'>,
     <guild.resourcedef.ResourceSource 'link-type'>,
     <guild.resourcedef.ResourceSource 'invalid-type'>,
     <guild.resourcedef.ResourceSource 'dir-copy'>,
     <guild.resourcedef.ResourceSource 'archive-dir-copy'>]

#### Default target type

The first source doesn't specify a target type. By default, target
type is 'link'.

    >>> default_type = test5_resdef.sources[0]
    >>> default_type.uri
    'file:test.txt'

    >>> print(default_type.target_type)
    None

Let's specify a run to resolve for so we can check the type of files
created.

    >>> run = runlib.for_dir(mkdtemp())

    >>> resolve(default_type, run)
    {'resolved': ['<project-dir>/test.txt'],
     'staged': ['test.txt'],
     'unpacked': []}

The resolved file:

    >>> resolved = path(run.dir, "test.txt")
    >>> cat(resolved)
    12345

The type of file resolved is a link:

    >>> islink(resolved), resolved
    (True, ...)

#### Copy target type

The second source explicitly specifies 'copy' as target type.

    >>> copy_type = test5_resdef.sources[1]
    >>> copy_type.uri
    'file:test.txt'

    >>> copy_type.target_type
    'copy'

    >>> run = runlib.for_dir(mkdtemp())

    >>> resolve(copy_type, run)
    {'resolved': ['<project-dir>/test.txt'],
     'staged': ['test.txt'],
     'unpacked': []}

The type of file resolved is a copy:

    >>> resolved = path(run.dir, "test.txt")
    >>> cat(resolved)
    12345

    >>> iscopy = lambda x: isfile(x) and not islink(x)
    >>> iscopy(resolved), resolved
    (True, ...)

#### Explicit link target type

The third source explicitly specifies 'link' as target type.

    >>> link_type = test5_resdef.sources[2]
    >>> link_type.uri
    'file:test.txt'

    >>> link_type.target_type
    'link'

    >>> run = runlib.for_dir(mkdtemp())

    >>> resolve(link_type, run)
    {'resolved': ['<project-dir>/test.txt'],
     'staged': ['test.txt'],
     'unpacked': []}

The type of file resolved is a link:

    >>> resolved = path(run.dir, "test.txt")
    >>> cat(resolved)
    12345

    >>> islink(resolved), resolved
    (True, ...)

#### Invalid target type

The fourth source defines an invalid target type.

    >>> invalid_type = test5_resdef.sources[3]
    >>> invalid_type.uri
    'file:test.txt'

    >>> invalid_type.target_type
    'invalid'

    >>> run = runlib.for_dir(mkdtemp())

    >>> resolve(invalid_type, run)
    Traceback (most recent call last):
    OpDependencyError: unsupported target-type 'invalid' in source invalid-type
    (expected 'link' or 'copy')

#### Copy resolved dirs

The next source specifies that a directory source by copied.

    >>> dir_copy = test5_resdef.sources[4]
    >>> dir_copy.uri
    'file:foo'

Nothing is selected, so we expect the directory itself to be copied.

    >>> dir_copy.select
    []

    >>> dir_copy.target_type
    'copy'

    >>> run = runlib.for_dir(mkdtemp())

    >>> resolve(dir_copy, run)
    {'resolved': ['<project-dir>/foo'],
     'staged': ['foo/a.txt', 'foo/bar/a.txt', 'foo/bar/b.txt'],
     'unpacked': []}

Each staged file is a copy:

    >>> iscopy(path(run.dir, "foo", "a.txt")), run.dir
    (True, ...)

    >>> iscopy(path(run.dir, "foo", "bar", "a.txt")), run.dir
    (True, ...)

    >>> iscopy(path(run.dir, "foo", "bar", "b.txt")), run.dir
    (True, ...)

#### Copy resolved dirs

The next source is a directory within an archive that's copied.

    >>> archive_dir_copy = test5_resdef.sources[5]
    >>> archive_dir_copy.uri
    'file:foo.zip'

The path `foo/bar` within the archive is selected.

    >>> archive_dir_copy.select
    [SelectSpec(pattern='foo/bar', reduce=None)]

The selection is copied.

    >>> archive_dir_copy.target_type
    'copy'

    >>> run = runlib.for_dir(mkdtemp())

    >>> with LogCapture() as log:
    ...     resolve(archive_dir_copy, run)
    {'resolved': ['<unpack-dir>/foo/bar'],
     'staged': ['bar/a.txt', 'bar/b.txt'],
     'unpacked': ['.guild-cache-foo.zip.unpacked',
                  'foo/a.txt',
                  'foo/bar/a.txt',
                  'foo/bar/b.txt']}

    >>> log.print_all()
    Unpacking .../samples/projects/resources/foo.zip

Each staged file is a copy:

    >>> iscopy(path(run.dir, "bar", "a.txt")), run.dir
    (True, ...)

    >>> iscopy(path(run.dir, "bar", "b.txt")), run.dir
    (True, ...)

### test6 resources

The `test6` resource illustrates the use of `preserve-path`, which

    >>> test6_resdef = res_model.get_resource("test6")
    >>> test6_resdef.sources
    [<guild.resourcedef.ResourceSource 'preserve-path'>,
     <guild.resourcedef.ResourceSource 'preserve-path-with-target'>]

#### Default preserve-path

The first source specifies `preserve-path`.

    >>> preserve_path = test6_resdef.sources[0]
    >>> preserve_path.preserve_path
    True

In this example, target-path is not specified.

    >>> print(preserve_path.target_path)
    None

Let's specify a run to resolve for so we can check the type of files
created.

    >>> run = runlib.for_dir(mkdtemp())

    >>> resolve(preserve_path, run)
    {'resolved': ['<project-dir>/foo/bar/a.txt'],
     'staged': ['foo/bar/a.txt'],
     'unpacked': []}

Note that the staged path includes the path from the project
directory.

#### Specifying preserve-path and target-path

Guild ignores target-path and shows a warning message when
preserve-path is specified.

    >>> preserve_path_with_target = test6_resdef.sources[1]
    >>> preserve_path_with_target.preserve_path
    True

In this case, target-path is specified.

    >>> preserve_path_with_target.target_path
    'bam'

When we resolve this source, we get a warning message.

    >>> run = runlib.for_dir(mkdtemp())

    >>> with LogCapture() as logs:
    ...     resolve(preserve_path_with_target, run)
    {'resolved': ['<project-dir>/foo/bar/b.txt'],
     'staged': ['foo/bar/b.txt'],
     'unpacked': []}

    >>> logs.print_all()
    WARNING: target-path 'bam' specified with preserve-path - ignoring

## Alternative resource defs

### Implicit sources

If a resource is defined as a list, the list is assumed to be the
resource sources.

    >>> gf = guildfile.for_string("""
    ... - model: m
    ...   resources:
    ...     res:
    ...       - file: foo.txt
    ...       - operation: bar
    ... """)

    >>> gf.default_model.get_resource("res").sources
    [<guild.resourcedef.ResourceSource 'file:foo.txt'>,
     <guild.resourcedef.ResourceSource 'operation:bar'>]

### Invalid data

    >>> guildfile.for_string("""
    ... - model: m
    ...   resources:
    ...     res: 123
    ... """)
    Traceback (most recent call last):
    GuildfileError: error in <string>: invalid resource value 123:
    expected a mapping or a list
