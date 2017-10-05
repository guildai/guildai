package(default_visibility = ["//visibility:public"])

py_library(
    name = "plugins",
    srcs = ["__init__.py"],
    deps = [
        ":cpu",
        ":disk",
        ":gpu",
        ":keras",
        ":memory",
    ],
)

py_library(
    name = "tensorflow",
    srcs = ["tensorflow.py"],
    deps = [
        "//guild:plugin",
    ],
)

py_library(
    name = "gpu",
    srcs = ["gpu.py"],
    deps = [
        ":tensorflow",
    ],
)

py_library(
    name = "keras",
    srcs = ["keras.py"],
    deps = [
        "//guild:plugin",
    ],
)

py_library(
    name = "cpu",
    srcs = ["cpu.py"],
    deps = [
        ":tensorflow",
        "@org_psutil",
    ],
)

py_library(
    name = "memory",
    srcs = ["memory.py"],
    deps = [
        ":tensorflow",
        "@org_psutil",
    ],
)

py_library(
    name = "disk",
    srcs = ["disk.py"],
    deps = [
        ":tensorflow",
        "@org_psutil",
    ],
)
