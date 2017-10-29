# Dependencies

Guild dependencies are managed by the `deps` module:

    >>> from guild import deps

The primary function of `deps` is to resolve dependencies defined in
operations.

To illustrate, we'll define a model operation that requires a
resource:

    >>> from guild import modelfile
    >>> mf = modelfile.from_string("""
    ... name: sample
    ... operations:
    ...  test:
    ...    cmd: <not used>
    ...    requires: data
    ... resources:
    ...   data:
    ...     sources:
    ...     - abc.txt
    ...     - file: def.txt
    ...     - url: http://foo.com/bar.tar.gz
    ...     - operation: foo/bar:baz
    ... """)

We can get the list of dependencies for an operation with the
`dependencies` attribute:

    >>> test_op = mf["sample"].get_operation("test")
    >>> test_op.dependencies
    [<guild.modelfile.OpDependency 'data'>]

The value of `requires` may be a single string or a list of
strings. Each string must be a reference to a model resource. Multiple
values indicate that all resources must be met.

Resource labels may be one of the following types:

- Resource in defined in the operation model
- Resource defined in anothet model in the modelfile
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
| common:data       | on resource `data` in model `common` in the modelfile |
| mnist/common:data | on `common:data` resource in package `mnist`          |
| mnist/data        | on `data` resource in package `mnist`                 |

Let's look at the required resource:

    >>> data_res = mf["sample"].get_resource("data")

This resource has the following sources:

    >>> data_res.sources
    [<guild.modelfile.ResourceSource 'file:abc.txt'>,
     <guild.modelfile.ResourceSource 'file:def.txt'>,
     <guild.modelfile.ResourceSource 'http://foo.com/bar.tar.gz'>,
     <guild.modelfile.ResourceSource 'operation:foo/bar:baz'>]

## Operation sources

The sample `data` resource above provides a source generated from an
operation. These are known as *operation sources*.

Operation sources must reference a model operation. The operation may
be defined for the source model, another model in the modelfile, or a
model defined in a package. Operation references must be in a format
that can be parsed using `op.OpRef.from_string`.

    >>> from guild.op import OpRef

`OpRef.from_string` returns a tuple of `OpRef` instance and any string
content following the reference.

Below are various examples.

Operation name only:

    >>> OpRef.from_string("foo")
    (OpRef(pkg_type=None,
           pkg_name=None,
           pkg_version=None,
           model_name=None,
           op_name='foo'), '')

Operation of a model in the same modelfile:

    >>> OpRef.from_string("foo:bar")
    (OpRef(pkg_type=None,
           pkg_name=None,
           pkg_version=None,
           model_name='foo',
           op_name='bar'), '')

Operation in a packaged model:

    >>> OpRef.from_string("foo/bar:baz")
    (OpRef(pkg_type=None,
           pkg_name='foo',
           pkg_version=None,
           model_name='bar',
           op_name='baz'), '')

Operations with various paths:

    >>> OpRef.from_string("foo/bar")
    (OpRef(pkg_type=None,
           pkg_name=None,
           pkg_version=None,
           model_name=None,
           op_name='foo'), '/bar')

    >>> OpRef.from_string("foo:bar/baz")
    (OpRef(pkg_type=None,
           pkg_name=None,
           pkg_version=None,
           model_name='foo',
           op_name='bar'), '/baz')

    >>> OpRef.from_string("foo/bar:baz/bam")
    (OpRef(pkg_type=None,
           pkg_name='foo',
           pkg_version=None,
           model_name='bar',
           op_name='baz'), '/bam')

Some invalid op references:

    >>> OpRef.from_string("")
    Traceback (most recent call last):
    OpRefError: invalid reference: ''
