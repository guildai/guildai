package(default_visibility = ["//visibility:public"])

py_library(
    name = "plugins",
    srcs = ["__init__.py"],
    deps = [
        ":gpu",
        ":keras",
    ],
)

py_library(
    name = "gpu",
    srcs = ["gpu.py"],
    deps = [
        "//guild:plugin",
    ],
)

py_library(
    name = "keras",
    srcs = ["keras.py"],
    deps = [
        "//guild:plugin",
    ],
)
