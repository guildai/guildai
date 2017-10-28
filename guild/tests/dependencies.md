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
    ...     sources: abcdef
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
    [<guild.modelfile.ResourceSource 'file:abcdef'>]
