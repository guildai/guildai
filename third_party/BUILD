package(default_visibility = ["//visibility:public"])

# The libraries below can be used to express a dependency on a third
# party library that must be available at runtime. These are typically
# installed via 'pip install' but may be available in other ways.

py_library(
    name = "pip"
)

py_library(
    name = "setuptools"
)

py_library(
    name = "twine"
)

py_library(
    name = "yaml"
)

# The aliases below are used to normalize our references to third
# party libraries.

alias(
    name = "click",
    actual = "@org_click",
)

alias(
    name = "tensorboard",
    actual = "@org_tensorflow_tensorboard//tensorboard",
)

alias(
    name = "psutil",
    actual = "@org_psutil",
)
