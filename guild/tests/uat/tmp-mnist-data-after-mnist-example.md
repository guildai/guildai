# Tmp MNIST data after `mnist` example

We want to confirm that none of the operations from the `mnist`
example resulted in the use of the default MNIST data location in
`$TEMP`.

    >>> run("find $TEMP/MNIST_data")
    find: .../MNIST_data...: No such file or directory
    <exit 1>
