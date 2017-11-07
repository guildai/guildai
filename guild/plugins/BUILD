package(default_visibility = ["//visibility:public"])

py_library(
    name = "plugins",
    srcs = ["__init__.py"],
    deps = [
        ":cloudml",
        ":cpu",
        ":disk",
        ":gpu",
        ":keras",
        ":memory",
    ],
)

py_library(
    name = "cloudml",
    srcs = ["cloudml.py"],
    deps = [
        "//guild:plugin",
        "//guild:plugin_util",
    ],
)

py_library(
    name = "cpu",
    srcs = ["cpu.py"],
    deps = [
        "//third_party:psutil",
        ":tensorflow_util",
    ],
)

py_library(
    name = "disk",
    srcs = ["disk.py"],
    deps = [
        "//third_party:psutil",
        ":tensorflow_util",
    ],
)

py_library(
    name = "gpu",
    srcs = ["gpu.py"],
    deps = [
        ":tensorflow_util",
    ],
)

py_library(
    name = "keras",
    srcs = ["keras.py"],
    deps = [
        "//guild:plugin",
        "//guild:plugin_util",
        ":python_util",
    ],
)

py_library(
    name = "memory",
    srcs = ["memory.py"],
    deps = [
        "//third_party:psutil",
        ":tensorflow_util",
    ],
)

py_library(
    name = "python_util",
    srcs = ["python_util.py"],
    deps = [
    ],
)

py_library(
    name = "tensorflow_util",
    srcs = ["tensorflow_util.py"],
    deps = [
        "//third_party:tensorflow",
        "//guild:plugin",
        ":python_util",
    ],
)
