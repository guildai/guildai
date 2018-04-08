# Prepare MNIST samples

MNIST samples are used to test deployed models. We can generate them
by running `mnist-samples:prepare`:

    >>> run("guild run mnist-samples:prepare -y count=4")
    Resolving mnist/dataset dependency
    ...
    Writing ./00001.png
    Writing ./00002.png
    Writing ./00003.png
    Writing ./00004.png
    Samples generated in ...
    Use /.../all.json for JSON instances in predict operations
    <exit 0>
