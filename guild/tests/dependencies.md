# Dependencies

Guild dependencies are managed by the `deps` module:

    >>> from guild import deps

The primary function of `deps` is to resolve dependencies defined in
operations.

To illustrate, we'll use a sample modelfile that defines various
dependencies.

    >>> from guild import modelfile
    >>> mf = modelfile.from_string("""
    ... name: sample
    ... operations:
    ...  test:
    ...    cmd: <not used>
    ...    requires: abcdef
    ... """)

This modefile defines a `sample` operation that has a single
dependency on `abcdef`. We can acces operation dependencies with the
`dependencies` opdef attribute:

    >>> test_op = mf["sample"].get_operation("test")
    >>> test_op.dependencies
    [<guild.modelfile.OpDependency 'abcdef'>]

The value for `requires` may be a string or a list of strings. A
string is interpreted as single dependency. A value may be a path to a
file or a label of a resources defined in the modelfile. In this case,
`abcdef` is a path.

Let's rewrite our modelfile to use a resource label as our dependency.

    >>> from guild import modelfile
    >>> mf = modelfile.from_string("""
    ... name: sample
    ... operations:
    ...  test:
    ...    cmd: <not used>
    ...    requires: :abcdef
    ... resources:
    ...   abcdef: abcdef
    ... """)

    >>> test_op = mf["sample"].get_operation("test")
    >>> test_op.dependencies
    [<guild.modelfile.OpDependency ':abcdef'>]
